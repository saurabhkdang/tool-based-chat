import os
from dotenv import load_dotenv

load_dotenv()

ACTIVE_MODULE = os.getenv("ACTIVE_MODULE", "sales")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4:31b-cloud")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or None