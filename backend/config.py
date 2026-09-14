import os
from dotenv import load_dotenv

load_dotenv()

ACTIVE_MODULE = os.getenv("ACTIVE_MODULE", "sales")