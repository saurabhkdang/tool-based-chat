from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from database import Employee, Customer, Order, OrderItem, Product, Category

def get_employee_info(db: Session, emp_id: int):
  print(emp_id)
  emp = db.query(Employee).filter(Employee.employee_id == emp_id).first()
  print(emp)
  if emp:
    return {"name" : emp.name, "department": emp.department, "salary" : emp.salary, "hire_date": emp.hire_date}
  return {"error" : "Employee not found"}

def list_all_employees(db: Session):
  employees = db.query(Employee).all()
  return [{"id" : e.employee_id, "name" : e.name, "department" : e.department, "salary" : e.salary, "hire_date": e.hire_date } for e in employees]

def get_customer_history(db: Session, customer_id: int = None, customer_name: str = None):
    query = db.query(Customer)
    if customer_id:
       query = query.filter(Customer.customer_id == customer_id)
    elif customer_name:
       query = query.filter(Customer.first_name.ilike(f"%{customer_name}%"))

    customer = query.first()
    if not customer:
       return {"error" : "Customer not found"}

    orders = db.query(Order).filter(Order.customer_id == customer.customer_id).all()
    return {
      "customer_name" : customer.first_name,
      "email" : customer.email,
      "order_count" : len(orders),
      "orders" : [{ "order_id": o.order_id, "date" : o.order_date, "status" : o.status } for o in orders]
    }

def get_order_details(db: Session, order_id: int):
  order = db.query(Order).filter(Order.order_id == order_id).first()
  if not order:
    return {"error" : "Order not found"}

  items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
  product_list = []
  for item in items:
    product = db.query(Product).filter(Product.product_id == item.product_id).first()
    product_list.append({
        "product_name" : product.product_name if product else "Unknown",
        "quantity": item.quantity,
        "price": item.unit_price
    })

  return {
     "order_id" : order.order_id,
     "customer_id" : order.customer_id,
     "status": order.status,
     "items": product_list
  }

def search_products(db: Session, product_name: str = None, category_name: str = None):
  query = db.query(Product).join(Category)
  if product_name:
    query = query.filter(Product.product_name.ilike(f"%{product_name}%"))
  if category_name:
    query = query.filter(Category.category_name.ilike(f"%{category_name}%"))

  products = query.all()
  print(f"Products : {products} ")
  return [{"id": p.product_id, "name": p.product_name, "price": p.price, "category": p.category.category_name} for p in products]

def get_sales_summary(db: Session):
  total_revenue = db.query(func.sum(OrderItem.quantity * OrderItem.unit_price)).scalar()
  total_orders = db.query(Order).count()

  return {
    "total_revenue" : total_revenue or 0,
    "total_orders": total_orders
  }

def get_batch_customer_orders(db: Session, customers: list = []):
  if not customers:
    return {"error" : "No customers names provided"}

  # Use or_ to find ANY of the names in the list
  filters = [Customer.first_name.ilike(f"%{c}%") for c in customers]
  customer_details = db.query(Customer).filter(or_(*filters)).all()
  
  results = {}
  for c in customer_details:
      # For each found customer, get their orders
      orders = db.query(Order).filter(Order.customer_id == c.customer_id).all()
      results[c.first_name] = [{ "order_id": o.order_id, "status": o.status } for o in orders]
      
  return results

def search_customers(db: Session, city: str = None, name: str = None):
    """
    Search for customers based on city or name. 
    Use this for prompts like 'Customers from Delhi' or 'Search for customer X'.
    """
    query = db.query(Customer)
    if city:
        query = query.filter(Customer.city.ilike(f"%{city}%"))
    if name:
        query = query.filter(Customer.first_name.ilike(f"%{name}%"))
    
    results = query.all()
    return [{"id": c.customer_id, "name": c.first_name, "city": c.city, "email": c.email} for c in results]

def search_orders(db: Session, status: str = None, customer_id: int = None):
    """
    Search for orders based on status (e.g., 'Pending', 'Shipped') or customer ID.
    Use this for prompts like 'Show me all pending orders'.
    """
    query = db.query(Order)
    if status:
        query = query.filter(Order.status.ilike(f"%{status}%"))
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    
    results = query.all()
    return [{"order_id": o.order_id, "status": o.status, "date": o.order_date, "customer_id": o.customer_id} for o in results]

def get_customers_by_product(db: Session, product_name: str):
    """
    Finds all customers who have purchased a specific product.
    Use this for prompts like 'Who ordered the wireless mouse?'.
    """
    # Join Customers -> Orders -> OrderItems -> Products
    results = db.query(Customer).join(Order).join(OrderItem).join(Product).\
               filter(Product.product_name.ilike(f"%{product_name}%")).all()
    
    return [{"id": c.customer_id, "name": c.first_name, "email": c.email} for c in results]


AVAILABLE_TOOLS = {
  "get_employee_info": get_employee_info,
  "list_all_employees": list_all_employees,
  "get_customer_history": get_customer_history,
  "get_order_details": get_order_details,
  "search_products": search_products,
  "get_sales_summary": get_sales_summary,
  "get_batch_customer_orders": get_batch_customer_orders,
  "search_customers": search_customers,
  "search_orders": search_orders,
  "get_customers_by_product": get_customers_by_product
}