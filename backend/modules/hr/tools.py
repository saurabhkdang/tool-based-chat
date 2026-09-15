from modules.hr.functions import query_employees, query_job_description, query_attendances

SYSTEM_PROMPT = "You are a professional HR assistant. Help users look up employee records, reporting hierarchy, job descriptions, and related HR information. When you receive data from a tool, summarize it clearly and naturally. Never return an empty response if the tool returned data. When a tool result contains a numeric value, state that exact number in your response - never recalculate, round, or guess a number yourself."

DISPLAY_NAME = "AI HR Assistant"
DISPLAY_SUBTITLE = "Ask about employees, hierarchy, attendance & job descriptions"
WELCOME_MESSAGE = 'Hello! I can help you look up employees, reporting hierarchy, attendance and job descriptions. Try asking "Who reports to Manoj?" or "Show me pending leave records".'

AVAILABLE_TOOLS = {
  "query_employees" : query_employees,
  "query_job_description" : query_job_description,
  "query_attendances" : query_attendances
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
            "joined_month": {"type": "integer", "description": "Filter to employees who joined in this month (1-12), regardless of year"},
            "joined_day": {"type": "integer", "description": "Filter to employees who joined on this day of the month (1-31), regardless of year/month"},
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
  },
  {
      "type": "function",
      "function": {
        "name": "query_attendances",
        "description": "Search employees attendances",
        "parameters": {
          "type": "object",
          "properties": {
            "emp_id": {"type": "integer", "description": "employee id to search for"},
            "attendance_status": {"type": "string", "description": "Filter by attendance status, e.g. 'Present', 'Privilege Leave', 'Sick Leave'"},
            "date_from": {"type": "string", "description": "Only include attendance records on/after this date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "Only include attendance records on/before this date (YYYY-MM-DD)"}
          }
        }
      }
    }
]
