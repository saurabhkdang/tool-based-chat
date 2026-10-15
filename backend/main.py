from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI
import json
import os
import uuid
import logging
from datetime import date
from dotenv import load_dotenv
import importlib
import config

tools = importlib.import_module(f"modules.{config.ACTIVE_MODULE}.tools")
database = importlib.import_module(f"modules.{config.ACTIVE_MODULE}.database")

get_db = database.get_db
init_db = database.init_db

load_dotenv()

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s",
  handlers=[
    logging.FileHandler("logs/chat.log", encoding="utf-8"),
    logging.StreamHandler()
  ]
)
logger = logging.getLogger("chatbot")

def _truncate(value, limit=2000):
  text = str(value)
  return text if len(text) <= limit else text[:limit] + f"...[truncated, {len(text)} chars total]"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins. For production, replace "*" with ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

client = OpenAI(
    base_url=config.LLM_BASE_URL,
    api_key=config.LLM_API_KEY
)

@app.on_event("startup")
def on_startup():
  init_db()

class ChatRequest(BaseModel):
  message: str
  history: list = []

@app.get("/module-info")
def module_info():
  return {
    "name": getattr(tools, "DISPLAY_NAME", "AI Assistant"),
    "subtitle": getattr(tools, "DISPLAY_SUBTITLE", ""),
    "welcome_message": getattr(tools, "WELCOME_MESSAGE", "Hello! How can I help you today?")
  }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):

  request_id = uuid.uuid4().hex[:8]
  logger.info(f"[{request_id}] Prompt: {request.message}")

  today_str = date.today().strftime("%Y-%m-%d")
  system_message = {
    "role": "system",
    "content": f"{tools.SYSTEM_PROMPT}\n\nToday's date is {today_str}. Use this to correctly resolve relative dates like 'this month', 'last week', 'this year', etc. Always use the \"16 Sept 2026\" format for all dates while displaying"
  }

  messages = [system_message] + request.history + [{"role" : "user", "content": request.message}]

  def stream_reply():
    # Use a loop to allow the AI to make multiple sequential tool calls (Reasoning Loop)
    while True:
      stream = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        tools=tools.TOOL_DEFINITIONS,
        tool_choice="auto",
        stream=True
      )

      content_acc = ""
      tool_calls_acc = {}

      for chunk in stream:
        delta = chunk.choices[0].delta

        if delta.content:
          content_acc += delta.content
          yield delta.content

        if delta.tool_calls:
          for tc in delta.tool_calls:
            entry = tool_calls_acc.setdefault(tc.index, {"id": None, "name": "", "arguments": ""})
            if tc.id:
              entry["id"] = tc.id
            if tc.function and tc.function.name:
              entry["name"] += tc.function.name
            if tc.function and tc.function.arguments:
              entry["arguments"] += tc.function.arguments

      if not tool_calls_acc:
        # AI has finished reasoning and streamed its final answer
        logger.info(f"[{request_id}] Final response: {_truncate(content_acc)}")
        break

      # AI wants to call tools, so we record the request and execute them
      messages.append({
        "role": "assistant",
        "content": content_acc or None,
        "tool_calls": [
          {
            "id": tc["id"],
            "type": "function",
            "function": {"name": tc["name"], "arguments": tc["arguments"]}
          } for tc in tool_calls_acc.values()
        ]
      })

      for tc in tool_calls_acc.values():
        function_name = tc["name"]
        try:
          args = json.loads(tc["arguments"]) if tc["arguments"] else {}
        except json.JSONDecodeError:
          logger.warning(f"[{request_id}] Could not parse arguments for {function_name}: {tc['arguments']}")
          args = {}

        logger.info(f"[{request_id}] Tool call: {function_name}({args})")

        if function_name in tools.AVAILABLE_TOOLS:
          tool_func = tools.AVAILABLE_TOOLS[function_name]
          try:
            result = tool_func(db=db, **args)
          except Exception as e:
            logger.error(f"[{request_id}] Tool {function_name} raised: {e}")
            result = {"error": f"Tool '{function_name}' failed: {e}"}
        else:
          logger.warning(f"[{request_id}] Unknown tool requested: {function_name}")
          result = {"error": f"Unknown tool '{function_name}'"}

        result_count = len(result) if isinstance(result, list) else None
        logger.info(f"[{request_id}] Tool result ({result_count} rows): {_truncate(result)}" if result_count is not None else f"[{request_id}] Tool result: {_truncate(result)}")

        messages.append({
          "role": "tool",
          "tool_call_id": tc["id"],
          "name": function_name,
          "content": str(result)
        })

  return StreamingResponse(stream_reply(), media_type="text/plain")