from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from modules.sales.database import Employee, Customer, Order, OrderItem, Product, Category

def query_employees(db: Session, employee_id: int = None, name: str = None, department: str = None,
                     min_salary: float = None, max_salary: float = None, manager_id: int = None,
                     hired_after: str = None, hired_before: str = None):
    query = db.query(Employee)
    if employee_id:
        query = query.filter(Employee.employee_id == employee_id)
    if name:
        query = query.filter(Employee.name.ilike(f"%{name}%"))
    if department:
        query = query.filter(Employee.department.ilike(f"%{department}%"))
    if min_salary is not None:
        query = query.filter(Employee.salary >= min_salary)
    if max_salary is not None:
        query = query.filter(Employee.salary <= max_salary)
    if manager_id is not None:
        query = query.filter(Employee.manager_id == manager_id)
    if hired_after:
        query = query.filter(Employee.hire_date >= hired_after)
    if hired_before:
        query = query.filter(Employee.hire_date <= hired_before)

    employees = query.all()
    if not employees:
        return {"error": "No employees found matching the given criteria"}
    return [{
        "id": e.employee_id, "name": e.name, "department": e.department,
        "salary": e.salary, "manager_id": e.manager_id, "hire_date": e.hire_date
    } for e in employees]

def query_customers(db: Session, customer_id: int = None, name: str = None, names: list = None,
                     email: str = None, city: str = None, signup_after: str = None,
                     signup_before: str = None, product_name: str = None, include_orders: bool = False):
    query = db.query(Customer)
    if product_name:
        query = query.join(Order).join(OrderItem).join(Product).filter(Product.product_name.ilike(f"%{product_name}%"))
    if customer_id:
        query = query.filter(Customer.customer_id == customer_id)
    if name:
        query = query.filter(Customer.first_name.ilike(f"%{name}%"))
    if names:
        query = query.filter(or_(*[Customer.first_name.ilike(f"%{n}%") for n in names]))
    if email:
        query = query.filter(Customer.email.ilike(f"%{email}%"))
    if city:
        query = query.filter(Customer.city.ilike(f"%{city}%"))
    if signup_after:
        query = query.filter(Customer.signup_date >= signup_after)
    if signup_before:
        query = query.filter(Customer.signup_date <= signup_before)

    customers = query.distinct().all()
    if not customers:
        return {"error": "No customers found matching the given criteria"}

    results = []
    for c in customers:
        entry = {"id": c.customer_id, "name": c.first_name, "email": c.email, "city": c.city, "signup_date": c.signup_date}
        if include_orders:
            orders = db.query(Order).filter(Order.customer_id == c.customer_id).all()
            entry["orders"] = [{"order_id": o.order_id, "date": o.order_date, "status": o.status} for o in orders]
        results.append(entry)
    return results

def query_orders(db: Session, order_id: int = None, customer_id: int = None, status: str = None,
                  date_from: str = None, date_to: str = None, product_name: str = None):
    query = db.query(Order)
    if product_name:
        query = query.join(OrderItem).join(Product).filter(Product.product_name.ilike(f"%{product_name}%"))
    if order_id:
        query = query.filter(Order.order_id == order_id)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if status:
        query = query.filter(Order.status.ilike(f"%{status}%"))
    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)

    orders = query.distinct().all()
    if not orders:
        return {"error": "No orders found matching the given criteria"}

    results = []
    for o in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == o.order_id).all()
        item_list = []
        for item in items:
            product = db.query(Product).filter(Product.product_id == item.product_id).first()
            item_list.append({
                "product_name": product.product_name if product else "Unknown",
                "quantity": item.quantity,
                "price": item.unit_price
            })
        results.append({
            "order_id": o.order_id, "customer_id": o.customer_id,
            "status": o.status, "date": o.order_date, "items": item_list
        })
    return results

def query_products(db: Session, product_id: int = None, name: str = None, category: str = None,
                    min_price: float = None, max_price: float = None, in_stock: bool = None):
    query = db.query(Product).join(Category)
    if product_id:
        query = query.filter(Product.product_id == product_id)
    if name:
        query = query.filter(Product.product_name.ilike(f"%{name}%"))
    if category:
        query = query.filter(Category.category_name.ilike(f"%{category}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock is True:
        query = query.filter(Product.stock_quantity > 0)
    elif in_stock is False:
        query = query.filter(Product.stock_quantity <= 0)

    products = query.all()
    if not products:
        return {"error": "No products found matching the given criteria"}
    return [{
        "id": p.product_id, "name": p.product_name, "price": p.price,
        "stock": p.stock_quantity, "category": p.category.category_name
    } for p in products]

def get_sales_summary(db: Session):
    total_revenue = db.query(func.sum(OrderItem.quantity * OrderItem.unit_price)).scalar()
    total_orders = db.query(Order).count()
    # print(f" orders : {total_orders}")
    return {
        "total_revenue": total_revenue or 0,
        "total_orders": total_orders
    }

SYSTEM_PROMPT = "You are a professional business assistant. When you receive data from a tool, summarize it clearly and naturally for the user. If you find multiple orders or items, list them clearly. Never return an empty response if the tool returned data. When a tool result contains a numeric value (counts, totals, prices, revenue), state that exact number in your response - never recalculate, round, or guess a number yourself."

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