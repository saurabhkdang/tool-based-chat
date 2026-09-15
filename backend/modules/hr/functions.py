from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, or_, extract
from modules.hr.database import Employee, JobDescription, Attendance, AttendanceStatus

def query_employees(db: Session, id: int = None, name: str = None, email: str = None, manager_name: str = None, status: bool = None, under_manager_id: int = None, born_after: str = None, born_before: str = None, birth_month: str = None, birth_day: str = None, joined_after: str = None, joined_before: str = None, joined_month: str = None, joined_day: str = None, city: str = None, state: str = None, department: str = None, buddy_name: str = None, having_jd_id: int = None):
  query = db.query(Employee)

  if under_manager_id:
    query = query.filter(Employee.parent_path.ilike(f"%/{under_manager_id}/%"))

  if manager_name:
    Manager = aliased(Employee)
    query = query.join(Manager, Employee.report_to == Manager.id).filter(Manager.name.ilike(f"%{ manager_name }%"))

  if buddy_name:
      Buddy = aliased(Employee)
      query = query.join(Buddy, Employee.buddy == Buddy.id).filter(Buddy.name.ilike(f"%{ buddy_name }%"))

  if id:
    query = query.filter(Employee.id == id)
  if name:
    query = query.filter(Employee.name.ilike(f"%{name}%"))
  if email:
    query = query.filter(Employee.email.ilike(f"%{email}%"))
  if status is not None:
    query = query.filter(Employee.status == (1 if status else 0))
  if department:
    query = query.filter(Employee.department.ilike(f"%{department}%"))
  if city:
    query = query.filter(Employee.city.ilike(f"%{city}%"))
  if state:
    query = query.filter(Employee.state.ilike(f"%{state}%"))
  if joined_after:
    query = query.filter(Employee.doj >= joined_after)
  if joined_before:
    query = query.filter(Employee.doj <= joined_before)
  if joined_month:
    query = query.filter(extract('month', Employee.doj) == joined_month)
  if joined_day:
    query = query.filter(extract('day', Employee.doj) == joined_day)
  if born_after:
    query = query.filter(Employee.dob >= born_after)
  if born_before:
    query = query.filter(Employee.dob <= born_before)
  if birth_month:
    query = query.filter(extract('month', Employee.dob) == birth_month)
  if birth_day:
    query = query.filter(extract('day', Employee.dob) == birth_day)
  if having_jd_id is not None:
    query = query.filter(Employee.jd_id == having_jd_id)


  employees = query.all()
  if not employees:
    return {"error" : "No employees found matching the given criteria"}
  return [{
    "id": e.id, "name" : e.name, "email": e.email, "manager": e.manager.name, "doj": e.doj, "department": e.department, "city": e.city
  } for e in employees]

def query_job_description(db: Session, job_title: str = None, include_employees: bool = False):
  query = db.query(JobDescription)
  if job_title:
    query = query.filter(JobDescription.job_title.ilike(f"%{job_title}%"))

  jds = query.all()
  if not jds:
    return  {"error" : "No Job descriptions found matching the given criteria"}

  results = []
  for j in jds:
    entry = {"id" : j.id, "job_title" : j.job_title}
    if include_employees:
      emps = db.query(Employee).filter(Employee.jd_id == j.id).all()
      entry["employees"] = [{"id" : e.id, "name" : e.name, "email" : e.email } for e in emps]
    results.append(entry)
  return results

def query_attendances(db: Session, emp_id: int = None, attendance_status: str = None, date_from : str = None, date_to : str = None):

  query = db.query(Attendance)

  if emp_id:
    query = query.filter(Attendance.user_id == emp_id)
  if date_from:
      query = query.filter(Attendance.attendance_date >= date_from)
  if date_to:
    query = query.filter(Attendance.attendance_date <= date_to)
  if attendance_status:
    matched_status = next(
      (s for s in AttendanceStatus if s.value.lower() == attendance_status.lower()),
      None
    )
    if matched_status:
      query = query.filter(Attendance.status == matched_status )
    if not matched_status:
      return {"error": f"Unknown attendance status: '{attendance_status}'"}

  attendances = query.all()

  return [{ "attendance_date" : a.attendance_date, "attendance_status" : a.status, "attendance_value" : a.status_value } for a in attendances]
