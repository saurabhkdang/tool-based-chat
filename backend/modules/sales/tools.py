from modules.sales.functions import query_employees, query_customers, query_orders, query_products, get_sales_summary

SYSTEM_PROMPT = "You are a professional business assistant. When you receive data from a tool, summarize it clearly and naturally for the user. If you find multiple orders or items, list them clearly. Never return an empty response if the tool returned data. When a tool result contains a numeric value (counts, totals, prices, revenue), state that exact number in your response - never recalculate, round, or guess a number yourself."

DISPLAY_NAME = "AI Business Assistant"
DISPLAY_SUBTITLE = "Ask about employees, customers, orders & products"
WELCOME_MESSAGE = 'Hello! I can help you look up employees, customers, orders and products. Try asking "Who are the employees in Sales?" or "Show me pending orders".'

AVAILABLE_TOOLS = {
    "query_employees": query_employees,
    "query_customers": query_customers,
    "query_orders": query_orders,
    "query_products": query_products,
    "get_sales_summary": get_sales_summary
}

TOOL_DEFINITIONS = [
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
