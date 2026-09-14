from sqlalchemy import create_engine, Column, Integer, String, Text, Date, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Employee(Base):
  __tablename__ = "employees"
  employee_id = Column(Integer, primary_key=True, index=True)
  name = Column(String(50))
  department = Column(String(50))
  salary = Column(Integer)
  manager_id = Column(Integer)
  hire_date = Column(Date)

class Category(Base):
  __tablename__ = "categories"
  category_id = Column(Integer, primary_key=True, index=True)
  category_name = Column(String(50), unique=True)
  products = relationship("Product", back_populates="category")

class Product(Base):
  __tablename__ = "products"
  product_id = Column(Integer, primary_key=True, index=True)
  product_name = Column(String(50))
  category_id = Column(Integer, ForeignKey("categories.category_id"))
  price = Column(Float)
  stock_quantity = Column(Integer)
  category = relationship("Category", back_populates="products")
  order_items = relationship("OrderItem", back_populates="product")

class Customer(Base):
  __tablename__ = "customers"
  customer_id = Column(Integer, primary_key=True, index=True)
  first_name = Column(String(50))
  last_name = Column(String(50))
  email = Column(String(50))
  city = Column(String(50))
  signup_date = Column(Date)
  orders = relationship("Order", back_populates="customer")

class Order(Base):
  __tablename__ = "orders"
  order_id = Column(Integer, primary_key=True, index=True)
  customer_id = Column(Integer, ForeignKey("customers.customer_id"))
  order_date = Column(Date)
  status = Column(String(20))
  customer = relationship("Customer", back_populates="orders")
  items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

def init_db():
  Base.metadata.create_all(bind=engine)

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()