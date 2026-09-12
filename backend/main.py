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
      "type" : "function",
      "function" : {
        "name" : "get_employee_info",
        "description" : "Fetches detailed info about an employee from the database using their emp_id",
        "parameters" : {
          "type" : "object",
          "properties": {
            "emp_id": {"type" : "integer", "description": "The ID of the employee"}
          },
          "required": ["emp_id"]
        }
      }
    },
    {
      "type" : "function",
      "function": {
        "name" : "list_all_employees",
        "description" : "Returns a list of all employees in the system",
        "parameters": {"type": "object", "properties" : {}}
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_customer_history",
        "description": "Fetches customer profile and their full order history. Use this when asked about a specific customer's orders or contact info.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer", "description": "The unique ID of the customer"},
                "customer_name": {"type": "string", "description": "The name of the customer"}
            }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_order_details",
        "description": "Retrieves full details of a specific order, including every product and quantity purchased in that order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "The unique ID of the order"}
            },
            "required": ["order_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "search_products",
        "description": "Searches for products based on name or category. Use this to find available items, prices, or categories.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "The name of the product"},
                "category_name": {"type": "string", "description": "The name of the category"}
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
    },
    {
      "type": "function",
      "function": {
        "name": "get_batch_customer_orders",
        "description": "Use this when the user asks for orders of multiple people at once (e.g., 'Orders for Priya and Amit'). Takes a list of names.",
        "parameters": {
          "type": "object",
          "properties": {
              "customers": {
                  "type": "array",
                  "items": {"type": "string"},
                  "description": "A list of customer names to search for"
              }
          },
          "required": ["customers"]
        }
      }
    },
    # Add these to your tool_definitions array in main.py
    {
        "type": "function",
        "function": {
            "name": "search_customers",
            "description": "Search for customers based on city or name. Use this for location-based or name-based customer searches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city to filter by"},
                    "name": {"type": "string", "description": "The name of the customer"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_orders",
            "description": "Search for orders based on status (e.g., 'Pending', 'Shipped') or customer ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "The order status to filter by"},
                    "customer_id": {"type": "integer", "description": "The ID of the customer"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customers_by_product",
            "description": "Finds all customers who have purchased a specific product. Use this for prompts like 'Who bought the X product'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "The name of the product to search for"}
                },
                "required": ["product_name"]
            }
        }
    }
  ]

  system_message = {
      "role": "system", 
      "content": "You are a professional business assistant. When you receive data from a tool, summarize it clearly and naturally for the user. If you find multiple orders or items, list them clearly. Never return an empty response if the tool returned data."
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
    print(f"AI Decision: {response_message}")

    if not response_message.tool_calls:
      # AI has finished reasoning and is providing a final answer
      break

    # AI wants to call tools, so we record the request and execute them
    messages.append(response_message)

    for tool_call in response_message.tool_calls:
      print(f"Calling Tool: {tool_call.function.name} with args: {tool_call.function.arguments}")
      function_name = tool_call.function.name
      import json
      args = json.loads(tool_call.function.arguments)

      if function_name in tools.AVAILABLE_TOOLS:
        tool_func = tools.AVAILABLE_TOOLS[function_name]
        result = tool_func(db=db, **args)
        print(f"DB Result for {tool_call.function.name}: {result}")
        
        messages.append({
          "role": "tool",
          "tool_call_id": tool_call.id,
          "name": function_name,
          "content": str(result)
        })

  # Final result is the content of the last message after the loop breaks
  return {"response" : response_message.content}