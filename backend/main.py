from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI
import os
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
  
  # Use a loop to allow the AI to make multiple sequential tool calls (Reasoning Loop)
  while True:
    response = client.chat.completions.create(
      model="gemma4:31b-cloud",
      messages=messages,
      tools=tool_definitions,
      tool_choice="auto"
    )

    response_message = response.choices[0].message
    # print(f"AI Decision: {response_message}")

    if not response_message.tool_calls:
      # AI has finished reasoning and is providing a final answer
      break

    # AI wants to call tools, so we record the request and execute them
    messages.append(response_message)

    for tool_call in response_message.tool_calls:
      # print(f"Calling Tool: {tool_call.function.name} with args: {tool_call.function.arguments}")
      function_name = tool_call.function.name
      import json
      args = json.loads(tool_call.function.arguments)

      if function_name in tools.AVAILABLE_TOOLS:
        tool_func = tools.AVAILABLE_TOOLS[function_name]
        result = tool_func(db=db, **args)
        # print(f"DB Result for {tool_call.function.name}: {result}")
        
        messages.append({
          "role": "tool",
          "tool_call_id": tool_call.id,
          "name": function_name,
          "content": str(result)
        })

  # Final result is the content of the last message after the loop breaks
  return {"response" : response_message.content}