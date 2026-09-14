from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import tools
from database import get_db, init_db

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins. For production, replace "*" with ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

client = OpenAI(
    base_url="http://localhost:11434/v1", 
    api_key=os.getenv("OLLAMA_API_KEY")
)

@app.on_event("startup")
def on_startup():
  init_db()

class ChatRequest(BaseModel):
  message: str
  history: list = []

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
  tool_definitions = [
    {
      "type": "function",
      "function": {
        "name": "query_employees",
        "description": "Search for employees using any combination of filters. Use this for any employee-related question, e.g. a specific employee's details, employees in a department, salary range, or who reports to a given manager.",
        "parameters": {
          "type": "object",
          "properties": {
            "employee_id": {"type": "integer", "description": "The unique ID of the employee"},
            "name": {"type": "string", "description": "Full or partial name of the employee"},
            "department": {"type": "string", "description": "Department name to filter by"},
            "min_salary": {"type": "number", "description": "Minimum salary (inclusive)"},
            "max_salary": {"type": "number", "description": "Maximum salary (inclusive)"},
            "manager_id": {"type": "integer", "description": "ID of the manager to filter direct reports by"},
            "hired_after": {"type": "string", "description": "Only include employees hired on/after this date (YYYY-MM-DD)"},
            "hired_before": {"type": "string", "description": "Only include employees hired on/before this date (YYYY-MM-DD)"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "query_customers",
        "description": "Search for customers using any combination of filters. Use this for any customer-related question: a specific customer, customers by city/email, multiple customers by name, customers who bought a specific product, and optionally their order history.",
        "parameters": {
          "type": "object",
          "properties": {
            "customer_id": {"type": "integer", "description": "The unique ID of the customer"},
            "name": {"type": "string", "description": "Full or partial name of a single customer"},
            "names": {
              "type": "array",
              "items": {"type": "string"},
              "description": "A list of customer names, use this when asking about multiple customers at once"
            },
            "email": {"type": "string", "description": "Full or partial email address"},
            "city": {"type": "string", "description": "City to filter customers by"},
            "signup_after": {"type": "string", "description": "Only include customers who signed up on/after this date (YYYY-MM-DD)"},
            "signup_before": {"type": "string", "description": "Only include customers who signed up on/before this date (YYYY-MM-DD)"},
            "product_name": {"type": "string", "description": "Only include customers who have purchased this product"},
            "include_orders": {"type": "boolean", "description": "Set true to also include each customer's order history"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "query_orders",
        "description": "Search for orders using any combination of filters, always returning full item details. Use this for a specific order, orders by status/customer/date range, or orders containing a specific product.",
        "parameters": {
          "type": "object",
          "properties": {
            "order_id": {"type": "integer", "description": "The unique ID of the order"},
            "customer_id": {"type": "integer", "description": "ID of the customer who placed the order"},
            "status": {"type": "string", "description": "Order status to filter by, e.g. Pending, Shipped"},
            "date_from": {"type": "string", "description": "Only include orders placed on/after this date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "Only include orders placed on/before this date (YYYY-MM-DD)"},
            "product_name": {"type": "string", "description": "Only include orders that contain this product"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "query_products",
        "description": "Search for products using any combination of filters. Use this for product lookups, price ranges, category filtering, or stock availability.",
        "parameters": {
          "type": "object",
          "properties": {
            "product_id": {"type": "integer", "description": "The unique ID of the product"},
            "name": {"type": "string", "description": "Full or partial product name"},
            "category": {"type": "string", "description": "Category name to filter by"},
            "min_price": {"type": "number", "description": "Minimum price (inclusive)"},
            "max_price": {"type": "number", "description": "Maximum price (inclusive)"},
            "in_stock": {"type": "boolean", "description": "Set true for only in-stock products, false for only out-of-stock"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_sales_summary",
        "description": "Provides high-level business insights including total company revenue and total orders processed.",
        "parameters": {"type": "object", "properties": {}}
      }
    }
  ]

  system_message = {
      "role": "system",
      "content": "You are a professional business assistant. When you receive data from a tool, summarize it clearly and naturally for the user. If you find multiple orders or items, list them clearly. Never return an empty response if the tool returned data. When a tool result contains a numeric value (counts, totals, prices, revenue), state that exact number in your response - never recalculate, round, or guess a number yourself."
  }

  messages = [system_message] + request.history + [{"role" : "user", "content": request.message}]

  def stream_reply():
    # Use a loop to allow the AI to make multiple sequential tool calls (Reasoning Loop)
    while True:
      stream = client.chat.completions.create(
        model="gemma4:31b-cloud",
        messages=messages,
        tools=tool_definitions,
        tool_choice="auto",
        stream=True
      )

      content_acc = ""
      tool_calls_acc = {}

      for chunk in stream:
        delta = chunk.choices[0].delta

        if delta.content:
          content_acc += delta.content
          yield delta.content

        if delta.tool_calls:
          for tc in delta.tool_calls:
            entry = tool_calls_acc.setdefault(tc.index, {"id": None, "name": "", "arguments": ""})
            if tc.id:
              entry["id"] = tc.id
            if tc.function and tc.function.name:
              entry["name"] += tc.function.name
            if tc.function and tc.function.arguments:
              entry["arguments"] += tc.function.arguments

      if not tool_calls_acc:
        # AI has finished reasoning and streamed its final answer
        break

      # AI wants to call tools, so we record the request and execute them
      messages.append({
        "role": "assistant",
        "content": content_acc or None,
        "tool_calls": [
          {
            "id": tc["id"],
            "type": "function",
            "function": {"name": tc["name"], "arguments": tc["arguments"]}
          } for tc in tool_calls_acc.values()
        ]
      })

      for tc in tool_calls_acc.values():
        function_name = tc["name"]
        try:
          args = json.loads(tc["arguments"]) if tc["arguments"] else {}
        except json.JSONDecodeError:
          args = {}

        if function_name in tools.AVAILABLE_TOOLS:
          tool_func = tools.AVAILABLE_TOOLS[function_name]
          try:
            result = tool_func(db=db, **args)
          except Exception as e:
            result = {"error": f"Tool '{function_name}' failed: {e}"}
        else:
          result = {"error": f"Unknown tool '{function_name}'"}

        messages.append({
          "role": "tool",
          "tool_call_id": tc["id"],
          "name": function_name,
          "content": str(result)
        })

  return StreamingResponse(stream_reply(), media_type="text/plain")