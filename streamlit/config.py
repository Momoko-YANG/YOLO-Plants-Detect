import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

DB_PATH = BASE_DIR / "chat_system.db"
PROMPT_FILE = BASE_DIR / "prompt.txt"
