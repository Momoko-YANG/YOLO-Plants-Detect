import os
from pathlib import Path
from typing import Any, Dict, List

from pymysql.cursors import DictCursor

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

SHARED_DIR = PROJECT_ROOT / "shared"
UPLOADS_DIR = SHARED_DIR / "uploads"
DIST_DIR = SHARED_DIR / "dist"
WEIGHTS_DIR = SHARED_DIR / "weights"
RUNS_DIR = BASE_DIR / "runs"
VIDEO_DIR = RUNS_DIR / "video"
RESULT_IMG_PATH = RUNS_DIR / "result.jpg"

for path in (UPLOADS_DIR, WEIGHTS_DIR, RUNS_DIR, VIDEO_DIR):
    path.mkdir(parents=True, exist_ok=True)

DB_CONFIG: Dict[str, Any] = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "123456"),
    "database": os.getenv("MYSQL_DATABASE", "yolo_detect"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
}

SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT = int(os.getenv("SERVER_PORT", "9999"))

FALLBACK_USERS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "username": "admin",
        "password": "admin",
        "name": "张三",
        "sex": "男",
        "email": "123@qq.com",
        "tel": "1234567889",
        "role": "admin",
        "avatar": "https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif",
        "time": None,
    },
    {
        "id": 2,
        "username": "test",
        "password": "12345",
        "name": "张三",
        "sex": "男",
        "email": "123@qq.com",
        "tel": "1234567889",
        "role": "common",
        "avatar": "https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif",
        "time": None,
    },
]
