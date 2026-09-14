from sqlalchemy import create_engine, Column, Integer, String, Text, Date, Float, ForeignKey, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('HR_DB_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Employee(Base):
  __tablename__ = "api_users_hrdb"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(100))
  email = Column(String(150))
  report_to = Column(Integer, ForeignKey("api_users_hrdb.id"))
  manager = relationship("Employee", remote_side=[id], foreign_keys=[report_to])
  status = Column(Integer)
  parent_path = Column(String(50))
  doj = Column(Date)
  dob = Column(Date)
  city = Column(String(100))
  state = Column(String(100))
  buddy = Column(Integer, ForeignKey("api_users_hrdb.id"))
  buddy_name = relationship("Employee", remote_side=[id], foreign_keys=[buddy])
  department = Column(String(255))
  jd_id = Column(Integer, ForeignKey("api_job_description.id"))
  jd = relationship("JobDescription", back_populates="employees")

class JobDescription(Base):
  __tablename__ = "api_job_description"
  id = Column(Integer, primary_key=True, index=True)
  job_title = Column(String(200))
  employees = relationship("Employee", back_populates="jd")
  tasks = relationship("JobTasks", back_populates="jobdes")

class JobTasks(Base):
  __tablename__ = "hrdb_job_description_details"
  id = Column(Integer, primary_key=True, index=True)
  jd_id = Column(Integer, ForeignKey("api_job_description.id"))
  jobdes = relationship("JobDescription", back_populates="tasks")

def init_db():
  Base.metadata.create_all(bind=engine)

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()