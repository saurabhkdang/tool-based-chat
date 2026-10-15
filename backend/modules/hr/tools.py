from modules.hr.functions import query_employees, query_job_description, query_attendances, query_leaves, query_leave_count, aggregate, query_employee_monthly_rating

SYSTEM_PROMPT = "You are a professional HR assistant. Help users look up employee records, reporting hierarchy, job descriptions, and related HR information. When you receive data from a tool, summarize it clearly and naturally. Never return an empty response if the tool returned data. When a tool result contains a numeric value, state that exact number in your response - never recalculate, round, or guess a number yourself. Never invent or guess an employee id: when the user refers to someone by name, pass employee_name to the tool (or look them up with query_employees first). If a tool reports that multiple employees match a name, list the matches and ask the user which one they mean instead of picking one."

DISPLAY_NAME = "AI HR Assistant"
DISPLAY_SUBTITLE = "Ask about employees, hierarchy, attendance & job descriptions"
WELCOME_MESSAGE = 'Hello! I can help you look up employees, reporting hierarchy, attendance and job descriptions. Try asking "Who reports to Manoj?" or "Show me pending leave records".'

AVAILABLE_TOOLS = {
  "query_employees" : query_employees,
  "query_job_description" : query_job_description,
  "query_attendances" : query_attendances,
  "query_leaves" : query_leaves,
  "query_leave_count" : query_leave_count,
  "aggregate" : aggregate,
  "query_employee_monthly_rating" : query_employee_monthly_rating
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
      "description": "Search job descriptions/titles, and optionally list the employees assigned to each one and/or the detailed task breakdown (skills required, responsibilities, etc.). Use this for questions about job roles, job titles, who holds a given job description, or what a role actually involves.",
      "parameters": {
        "type": "object",
        "properties": {
          "job_title": {"type": "string", "description": "Full or partial job title to search for"},
          "include_employees": {"type": "boolean", "description": "Set true to also include the employees assigned to each matching job description"},
          "include_details": {"type": "boolean", "description": "Set true to also include the detailed task/skill breakdown for each matching job description"}
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
            "emp_id": {"type": "integer", "description": "Employee id, only if already known from a previous tool result"},
            "employee_name": {"type": "string", "description": "Full or partial employee name - use this when the user refers to someone by name"},
            "attendance_status": {"type": "string", "description": "Filter by attendance status, e.g. 'Present', 'Privilege Leave', 'Sick Leave'"},
            "date_from": {"type": "string", "description": "Only include attendance records on/after this date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "Only include attendance records on/before this date (YYYY-MM-DD)"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "query_leaves",
        "description": "Search employee leave records, including type, status, dates, and approval details. If a leave's dates conflict with actual attendance records (e.g. employee returned early and was marked present), this is flagged in the result. Use this for questions about leave requests, leave balances, or approval status.",
        "parameters": {
          "type": "object",
          "properties": {
            "emp_id": {"type": "integer", "description": "Employee id, only if already known from a previous tool result"},
            "employee_name": {"type": "string", "description": "Full or partial employee name - use this when the user refers to someone by name"},
            "leave_status": {"type": "string", "description": "Filter by leave approval status: 'approved', 'pending', or 'rejected'"},
            "leave_date_from": {"type": "string", "description": "Only include leaves starting on/after this date (YYYY-MM-DD)"},
            "leave_end_to": {"type": "string", "description": "Only include leaves ending on/before this date (YYYY-MM-DD)"},
            "added_on_from": {"type": "string", "description": "Only include leaves applied for on/after this date (YYYY-MM-DD)"},
            "added_on_to": {"type": "string", "description": "Only include leaves applied for on/before this date (YYYY-MM-DD)"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "query_leave_count",
        "description": "Get an employee's monthly leave balance metrics: opening/closing/availed/accrued counts for sick leave, casual leave, and privilege leave. Use this for questions about leave balances or how many leaves someone has used/remaining.",
        "parameters": {
          "type": "object",
          "properties": {
            "emp_id": {"type": "integer", "description": "Employee id, only if already known from a previous tool result"},
            "employee_name": {"type": "string", "description": "Full or partial employee name - use this when the user refers to someone by name"},
            "from_date": {"type": "string", "description": "Only include months on/after this date (YYYY-MM-DD)"},
            "to_date": {"type": "string", "description": "Only include months on/before this date (YYYY-MM-DD)"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "aggregate",
        "description": "Compute aggregate statistics (count, sum, average, min, max) over employees, attendances, leaves, or job descriptions, optionally grouped by a field and filtered. Always use this instead of manually counting/summing individual records for questions involving totals, counts, averages, or breakdowns by category.",
        "parameters": {
          "type": "object",
          "properties": {
            "entity": {
              "type": "string",
              "enum": ["employees", "attendances", "leaves", "job_description"],
              "description": "Which type of record to aggregate"
            },
            "aggregate_fn": {
              "type": "string",
              "enum": ["count", "sum", "avg", "min", "max"],
              "description": "The aggregation to perform. Use 'count' for how many records match the filters."
            },
            "field": {
              "type": "string",
              "description": "The field to sum/average/min/max over (not needed for 'count'), e.g. 'total_days'"
            },
            "group_by": {
              "type": "string",
              "description": "Optional field to group results by, returning one aggregate per group, e.g. 'attendance_status' or 'department'"
            },
            "filters": {
              "type": "object",
              "description": "Optional filters to narrow down records first, using the same filter names as that entity's query tool, e.g. {\"leave_status\": \"pending\"} or {\"date_from\": \"2026-09-01\", \"date_to\": \"2026-09-16\"}"
            }
          },
          "required": ["entity"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "query_employee_monthly_rating",
        "description": "Get an employee's monthly performance ratings, including the rating value and any manager comments. Use this for questions about performance reviews, ratings, or feedback history.",
        "parameters": {
          "type": "object",
          "properties": {
            "emp_id": {"type": "integer", "description": "Employee id, only if already known from a previous tool result"},
            "employee_name": {"type": "string", "description": "Full or partial employee name - use this when the user refers to someone by name"},
            "start_month": {"type": "string", "description": "Only include ratings on/after this date (YYYY-MM-DD)"},
            "end_month": {"type": "string", "description": "Only include ratings on/before this date (YYYY-MM-DD)"},
            "performance": {
              "type": "string",
              "enum": ["red", "yellow", "green", "none", "no_rating", "no_rating_other"],
              "description": "Filter by performance rating value"
            },
            "comment": {"type": "string", "description": "Search for ratings whose manager comment contains this text"},
            
          }
        }
      }
    }
]
