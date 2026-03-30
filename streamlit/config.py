import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

# 数据文件路径
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "chat_system.db"
PROMPT_FILE = DATA_DIR / "prompt.txt"

# 权重与输出路径
WEIGHTS_DIR = BASE_DIR / "weights"
RUNS_DIR = BASE_DIR / "runs"
