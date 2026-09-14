from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, or_, extract
from modules.hr.database import Employee, JobDescription

def query_employees(db: Session, id: int = None, name: str = None, email: str = None, manager_name: str = None, status: bool = None, under_manager_id: int = None, born_after: str = None, born_before: str = None, birth_month: str = None, birth_day: str = None, joined_after: str = None, joined_before: str = None, city: str = None, state: str = None, department: str = None, buddy_name: str = None, having_jd_id: int = None):
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
    "id": e.id, "name" : e.name, "email": e.email, "manager": e.manager.name
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

SYSTEM_PROMPT = {"role": "system", "content" : "You are a professional HR assistant. Help users look up employee records, reporting hierarchy, job descriptions, and related HR information. When you receive data from a tool, summarize it clearly and naturally. Never return an empty response if the tool returned data. When a tool result contains a numeric value, state that exact number in your response - never recalculate, round, or guess a number yourself."}

AVAILABLE_TOOLS = {
  "query_employees" : query_employees,
  "query_job_description" : query_job_description
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
            "id": {"type": "integer", "description": "The unique ID of the employee"},
            "name": {"type": "string", "description": "Full or partial name of the employee"},
            "email": {"type": "string", "description": "Email Id of the employee"},
            "manager_name": {"type": "string", "description": "Report manager name of the employee"},
            "status": {"type": "boolean", "description": "Filter by whether the employee is currently active (true) or inactive (false)"},
            "under_manager_id": {"type": "integer", "description": "Get all employees under this manager, at any level of the hierarchy"},
            "born_after": {"type": "string", "description": "Only include employees born on/after this date (YYYY-MM-DD)"},
            "born_before": {"type": "string", "description": "Only include employees born on/before this date (YYYY-MM-DD)"},
            "birth_month": {"type": "integer", "description": "Filter to employees born in this month (1-12), regardless of year"},
            "birth_day": {"type": "integer", "description": "Filter to employees born on this day of the month (1-31), regardless of year/month"},
            "joined_after": {"type": "string", "description": "Only include employees who joined on/after this date (YYYY-MM-DD)"},
            "joined_before": {"type": "string", "description": "Only include employees who joined on/before this date (YYYY-MM-DD)"},
            "city": {"type": "string", "description": "City the employee is based in"},
            "state": {"type": "string", "description": "State the employee is based in"},
            "department": {"type": "string", "description": "Department name to filter by"},
            "buddy_name": {"type": "string", "description": "Name of the employee's assigned buddy"},
            "having_jd_id": {"type": "integer", "description": "Filter to employees assigned to this job description ID"},
          }
        }
      }
  },
  {
    "type": "function",
    "function": {
      "name": "query_job_description",
      "description": "Search job descriptions/titles, and optionally list the employees currently assigned to each one. Use this for questions about job roles, job titles, or who holds a given job description.",
      "parameters": {
        "type": "object",
        "properties": {
          "job_title": {"type": "string", "description": "Full or partial job title to search for"},
          "include_employees": {"type": "boolean", "description": "Set true to also include the employees assigned to each matching job description"}
        }
      }
    }
  }
]