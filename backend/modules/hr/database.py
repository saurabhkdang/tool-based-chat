from sqlalchemy import create_engine, Column, Integer, String, Text, Date, Float, ForeignKey, DateTime, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from dotenv import load_dotenv
from enum import Enum as PyEnum

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
  attendances = relationship("Attendance", back_populates="employees")
  leaves = relationship("Leaves", back_populates="employees")

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

class AttendanceStatus(PyEnum):
  P = "Present"
  HF = "Half Day"
  LV = "Leave"
  FH = "Festive Holiday"
  WO = "Week Off"
  SL = "Sick Leave"
  SLHF = "Sick Leave Half Day"
  CL = "Casual Leave"
  CLHF = "Casual Leave Half Day"
  PL = "Privilege Leave"
  PLHF = "Privilege Leave Half Day"
  UL = "U"
  WFHFD = "Work From Home Full Day"
  WFHHF = "Work From Home Half Day"
  FHW = "Fest Holiday Working"
class Attendance(Base):
  __tablename__ = "hrdb_users_attendance"
  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("api_users_hrdb.id"))
  attendance_date = Column(Date)
  status = Column(Enum(AttendanceStatus, name="attendance_status"))
  status_value = Column(Float)
  employees = relationship("Employee", back_populates="attendances")

class Leaves(Base):
  __tablename__ = "hrdb_users_leaves"
  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("api_users_hrdb.id"))
  type_of_leave = Column(Enum(AttendanceStatus, name="attendance_status"))
  start_date = Column(Date)
  end_date = Column(Date)
  total_days = Column(Float)
  status = Column(Enum('approved','pending','rejected', name="leaves_status"))
  working_on = Column(String(500))
  reason = Column(String(500))
  action_date = Column(Date)
  action_comment = Column(String(500))
  employees = relationship("Employee", back_populates="leaves")

def init_db():
  Base.metadata.create_all(bind=engine)

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()