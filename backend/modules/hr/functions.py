from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, or_, extract
from modules.hr.database import Employee, JobDescription, Attendance, AttendanceStatus, Leaves, AttendanceMetrics

WORKING_ATTENDANCE_STATUSES = [
  AttendanceStatus.P,
  AttendanceStatus.HF,
  AttendanceStatus.WFHFD,
  AttendanceStatus.WFHHF,
  AttendanceStatus.FHW,
]

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

  return [{ "attendance_date" : a.attendance_date, "attendance_status" : a.status.value if a.status else None, "attendance_value" : a.status_value } for a in attendances]

def query_leaves(db: Session, emp_id: int = None, leave_status: str = None, leave_date_from: str = None, leave_end_to: str = None):

  query = db.query(Leaves)
  if emp_id:
    query = query.filter(Leaves.user_id == emp_id)
  if leave_date_from:
    query = query.filter(Leaves.start_date >= leave_date_from)
  if leave_end_to:
    query = query.filter(Leaves.end_date <= leave_end_to)
  if leave_status:
    query = query.filter(Leaves.status.ilike(leave_status))

  leaves = query.all()

  results = []
  for l in leaves:
    entry = { "type_of_leave" : l.type_of_leave.value if l.type_of_leave else None, "start_date" : l.start_date, "end_date" : l.end_date, "total_days" : l.total_days, "status" : l.status, "working_on" : l.working_on, "leave_reason" : l.reason, "leave_action_date" : l.action_date, "leave_action_comment" : l.action_comment, "employee_name" : l.employees.name, "emp_id" : l.user_id }

    if l.start_date and l.end_date:
      conflicts = db.query(Attendance).filter(
        Attendance.user_id == l.user_id,
        Attendance.attendance_date >= l.start_date,
        Attendance.attendance_date <= l.end_date,
        Attendance.status.in_(WORKING_ATTENDANCE_STATUSES)
      ).all()

      if conflicts:
        conflict_dates = ", ".join(str(c.attendance_date) for c in conflicts)
        entry["attendance_conflicts"] = f"Marked as working on {conflict_dates} despite this approved leave covering that period."
    results.append(entry)
  return results

def query_leave_count(db: Session, emp_id: int = None, from_date: str = None, to_date: str = None):
  query = db.query(AttendanceMetrics)
  if emp_id:
    query = query.filter(AttendanceMetrics.user_id == emp_id)
  if from_date:
    query = query.filter(AttendanceMetrics.month_year>= from_date)
  if to_date:
    query = query.filter(AttendanceMetrics.month_year<= to_date)

  leaves = query.all()

  return [{
    "user_id" : l.user_id,     "month_year" : l.month_year,     "closing_sl" : l.closing_sl,     "closing_cl" : l.closing_cl,     "closing_pl" : l.closing_pl,     "availed_sl" : l.availed_sl,     "availed_cl" : l.availed_cl,     "availed_pl" : l.availed_pl,     "accural_sl" : l.accural_sl,     "accural_cl" : l.accural_cl,     "accural_pl" : l.accural_pl,     "opening_sl" : l.opening_sl,     "opening_cl" : l.opening_cl,     "opening_pl" : l.opening_pl } for l in leaves]

ENTITY_FUNCTIONS = {
  "employees" : query_employees,
  "attendances" : query_attendances,
  "leaves" : query_leaves,
  "job_description" : query_job_description
}

def aggregate(db: Session, entity: str, aggregate_fn: str = "count", field: str = None, group_by: str = None, filters: dict = None):
  if entity not in ENTITY_FUNCTIONS:
    return {"error" : f"Unknown entity '{entity}'. Valid options : {list(ENTITY_FUNCTIONS.keys())} "}

  rows = ENTITY_FUNCTIONS[entity](db=db, **(filters or {}))
  if isinstance(rows, dict) and "error" in rows:
    return rows

  def compute(group_rows):
    if aggregate_fn == "count":
      return len(group_rows)
    values = [r.get(field) for r in group_rows if r.get(field) is not None]
    if not values:
      return 0
    if aggregate_fn == "sum":
      return sum(values)
    if aggregate_fn == "avg":
      return round(sum(values) / len(values), 2)
    if aggregate_fn == "min":
      return min(values)
    if aggregate_fn == "max":
      return max(values)
    
    return {"error" : f"Unknown aggregate_fn '{aggregate_fn}'"}

  if group_by:
    groups = {}
    for row in rows:
      key = row.get(group_by)
      groups.setdefault(key, []).append(row)
    return {str(k) : compute(v) for k, v in groups.items()}

  return {aggregate_fn: compute(rows)}