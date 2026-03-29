import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import cv2
import pymysql
import socketio
import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from pymysql.cursors import DictCursor
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
SPRING_FILES_DIR = PROJECT_ROOT / "yolo_img_detection_web" / "yolo_img_detection_springboot" / "files"
WEIGHTS_DIR = PROJECT_ROOT / "yolo_img_detection_web" / "yolo_img_detection_flask" / "weights"
RUNS_DIR = BASE_DIR / "runs"
VIDEO_DIR = RUNS_DIR / "video"
RESULT_IMG_PATH = RUNS_DIR / "result.jpg"

for path in (SPRING_FILES_DIR, WEIGHTS_DIR, RUNS_DIR, VIDEO_DIR):
    path.mkdir(parents=True, exist_ok=True)

DB_CONFIG = {
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

camera_recording = False
main_loop: Optional[asyncio.AbstractEventLoop] = None


class PredictRequest(BaseModel):
    startTime: Optional[str] = ""
    weight: Optional[str] = ""
    username: Optional[str] = ""
    inputImg: Optional[str] = ""
    kind: Optional[str] = ""
    conf: Optional[str] = ""


class SuggestRequest(BaseModel):
    result: Optional[str] = ""
    kind: Optional[str] = ""


class UserPayload(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = ""
    password: Optional[str] = ""
    name: Optional[str] = ""
    sex: Optional[str] = ""
    email: Optional[str] = ""
    tel: Optional[str] = ""
    role: Optional[str] = ""
    avatar: Optional[str] = ""
    time: Optional[str] = None


class ImgRecordPayload(BaseModel):
    id: Optional[int] = None
    weight: Optional[str] = ""
    inputImg: Optional[str] = ""
    outImg: Optional[str] = ""
    confidence: Optional[str] = ""
    allTime: Optional[str] = ""
    conf: Optional[str] = ""
    label: Optional[str] = ""
    username: Optional[str] = ""
    kind: Optional[str] = ""
    startTime: Optional[str] = ""


class VideoRecordPayload(BaseModel):
    id: Optional[int] = None
    weight: Optional[str] = ""
    inputVideo: Optional[str] = ""
    outVideo: Optional[str] = ""
    conf: Optional[str] = ""
    username: Optional[str] = ""
    kind: Optional[str] = ""
    startTime: Optional[str] = ""


class CameraRecordPayload(BaseModel):
    id: Optional[int] = None
    weight: Optional[str] = ""
    outVideo: Optional[str] = ""
    conf: Optional[str] = ""
    username: Optional[str] = ""
    kind: Optional[str] = ""
    startTime: Optional[str] = ""


def success(data: Any = None) -> Dict[str, Any]:
    return {"code": "0", "msg": "成功", "data": data}


def error(msg: str, code: str = "-1") -> Dict[str, Any]:
    return {"code": code, "msg": msg, "data": None}


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)  # pydantic v2
    return model.dict(exclude_none=True)  # pydantic v1


def get_conn() -> pymysql.Connection:
    return pymysql.connect(**DB_CONFIG)


def format_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def camel_to_snake(name: str) -> str:
    chars: List[str] = []
    for ch in name:
        if ch.isupper():
            chars.append("_" + ch.lower())
        else:
            chars.append(ch)
    return "".join(chars)


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for key, value in row.items():
        data[snake_to_camel(key)] = format_value(value)
    return data


def fetch_one(sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    finally:
        conn.close()


def fetch_all(sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def execute(sql: str, params: Optional[tuple] = None) -> int:
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(sql, params or ())
            conn.commit()
            return affected
    finally:
        conn.close()


def paginate_query(
    table: str,
    page_num: int,
    page_size: int,
    order_by: str,
    filters: List[tuple],
) -> Dict[str, Any]:
    where_sql = " WHERE 1=1"
    values: List[Any] = []
    for condition, value in filters:
        if value is not None and str(value).strip() != "":
            where_sql += f" AND {condition}"
            values.append(f"%{str(value).strip()}%")

    count_sql = f"SELECT COUNT(*) AS total FROM {table}{where_sql}"
    count_row = fetch_one(count_sql, tuple(values)) or {"total": 0}
    total = int(count_row.get("total", 0))

    offset = max(page_num - 1, 0) * page_size
    data_sql = (
        f"SELECT * FROM {table}{where_sql} "
        f"ORDER BY {order_by} DESC LIMIT %s OFFSET %s"
    )
    rows = fetch_all(data_sql, tuple(values + [page_size, offset]))
    records = [normalize_row(row) for row in rows]

    pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "records": records,
        "total": total,
        "size": page_size,
        "current": page_num,
        "pages": pages,
    }


def save_uploaded_file(upload_file: UploadFile) -> str:
    safe_name = os.path.basename(upload_file.filename or "upload.bin")
    file_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = SPRING_FILES_DIR / file_name

    with file_path.open("wb") as f:
        f.write(upload_file.file.read())

    return file_name


def build_file_url(file_name: str) -> str:
    return f"http://{SERVER_HOST}:{SERVER_PORT}/files/{file_name}"


def file_path_from_flag(flag: str) -> Optional[Path]:
    direct_path = SPRING_FILES_DIR / flag
    if direct_path.exists():
        return direct_path

    for item in SPRING_FILES_DIR.iterdir():
        if item.is_file() and flag in item.name:
            return item
    return None


def download_file(url: str, save_path: Path) -> None:
    import requests

    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with save_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def upload_local_file(local_path: Path) -> str:
    file_name = f"{uuid.uuid4().hex}_{local_path.name}"
    target = SPRING_FILES_DIR / file_name
    target.write_bytes(local_path.read_bytes())
    return build_file_url(file_name)


def emit_event(event: str, payload: Any, room: Optional[str] = None) -> None:
    if main_loop and main_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(
            sio.emit(event, {"data": payload}, room=room),
            main_loop,
        )
        try:
            future.result(timeout=5)
        except Exception as exc:
            print(f"socket emit error: {exc}")


def get_weight_names() -> List[str]:
    if not WEIGHTS_DIR.exists():
        return []
    return sorted([p.name for p in WEIGHTS_DIR.iterdir() if p.is_file()])


def convert_avi_to_mp4(avi_path: Path, mp4_path: Path) -> Generator[int, None, None]:
    cap = cv2.VideoCapture(str(avi_path))
    if not cap.isOpened():
        raise ValueError(f"无法打开AVI文件: {avi_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(str(mp4_path), fourcc, fps, (width, height))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(mp4_path), fourcc, fps, (width, height))

    if not out.isOpened():
        cap.release()
        raise ValueError(f"无法创建MP4文件: {mp4_path}")

    frame_count = 0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            frame_count += 1
            yield int((frame_count / total_frames) * 100)
        yield 100
    finally:
        cap.release()
        out.release()


def safe_json_loads(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return []


def run_image_predict(weight: str, img_url: str, kind: str, conf: float) -> Dict[str, Any]:
    start = time.time()
    tmp_name = f"{uuid.uuid4().hex}_input.jpg"
    input_path = RUNS_DIR / tmp_name

    download_file(img_url, input_path)

    weight_path = WEIGHTS_DIR / weight
    if not weight_path.exists():
        input_path.unlink(missing_ok=True)
        raise ValueError(f"权重不存在: {weight}")

    model = YOLO(str(weight_path))
    results = model.predict(source=str(input_path), conf=conf, half=True, save_conf=True)

    labels_map = {
        "plants": [
            "苹果黑星病叶", "苹果叶片", "苹果锈病叶", "甜椒叶片", "甜椒叶斑病叶", "蓝莓叶片", "樱桃叶片", "玉米灰斑病叶", "玉米叶枯病叶", "玉米锈病叶",
            "桃树叶片", "马铃薯叶片", "马铃薯早疫病叶", "马铃薯晚疫病叶", "覆盆子叶片", "大豆叶片（拼写变体）", "大豆叶片", "南瓜白粉病叶", "草莓叶片",
            "番茄早疫病叶", "番茄斑枯病叶", "番茄叶片", "番茄细菌性斑点病叶", "番茄晚疫病叶", "番茄花叶病毒病叶", "番茄黄化病毒病叶", "番茄霉病叶", "番茄二斑叶螨危害叶",
            "葡萄叶片", "葡萄黑腐病叶",
        ]
    }

    labels_dict = labels_map.get(kind, labels_map["plants"])
    output = {
        "labels": [],
        "confidences": [],
        "allTime": f"{(time.time() - start):.3f}秒",
    }

    if len(results) == 0:
        output["labels"] = "预测失败"
        output["confidences"] = "0.00%"
    else:
        for result in results:
            confidences = result.boxes.conf if hasattr(result.boxes, "conf") else []
            classes = result.boxes.cls if hasattr(result.boxes, "cls") else []
            if confidences.numel() == 0 or classes.numel() == 0:
                output["labels"] = "预测失败"
                output["confidences"] = "0.00%"
                break

            for cls, score in zip(classes, confidences):
                idx = int(cls)
                label = labels_dict[idx] if idx < len(labels_dict) else str(idx)
                output["labels"].append(label)
                output["confidences"].append(f"{float(score) * 100:.2f}%")

            result.save(filename=str(RESULT_IMG_PATH))

    out_url = ""
    if RESULT_IMG_PATH.exists():
        out_url = upload_local_file(RESULT_IMG_PATH)
        RESULT_IMG_PATH.unlink(missing_ok=True)

    input_path.unlink(missing_ok=True)

    return {
        "status": 200 if output["labels"] != "预测失败" else 400,
        "message": "预测成功" if output["labels"] != "预测失败" else "该图片无法识别，请重新上传！",
        "outImg": out_url,
        "allTime": output["allTime"],
        "confidence": json.dumps(output["confidences"], ensure_ascii=False),
        "label": json.dumps(output["labels"], ensure_ascii=False),
    }


def insert_record(table: str, payload: Dict[str, Any]) -> None:
    keys = [camel_to_snake(k) for k in payload.keys()]
    placeholders = ", ".join(["%s"] * len(keys))
    columns = ", ".join([f"`{k}`" for k in keys])
    values = tuple(payload.values())
    sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
    execute(sql, values)


def update_record(table: str, payload: Dict[str, Any], record_id: int) -> None:
    pairs: List[str] = []
    values: List[Any] = []
    for key, value in payload.items():
        if key == "id":
            continue
        col = camel_to_snake(key)
        pairs.append(f"`{col}`=%s")
        values.append(value)

    if not pairs:
        return

    values.append(record_id)
    sql = f"UPDATE `{table}` SET {', '.join(pairs)} WHERE id=%s"
    execute(sql, tuple(values))


def make_suggestion(result: str, kind: str = "") -> str:
    title = f"识别结果：{result}"
    kind_text = f"（分类：{kind}）" if kind else ""
    return (
        f"🌱 {title}{kind_text}<br><br>"
        "📌 可能原因：当前症状通常与环境湿度、通风不足或病原菌传播有关。<br><br>"
        "🧑‍🌾 种植建议：优先清理病叶、控制浇水频率、提升通风和光照，减少再次感染风险。<br><br>"
        "🛠️ 治理方式：先做小范围对照处理，再按7天一个周期复查；若扩散明显，及时更换药剂策略并隔离病株。"
    )


fastapi_app = FastAPI(title="YOLO FastAPI Backend")
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.on_event("startup")
async def on_startup() -> None:
    global main_loop
    main_loop = asyncio.get_running_loop()


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ, auth):
    await sio.emit("message", {"data": "Connected to WebSocket server!"}, room=sid)


@sio.event
async def disconnect(sid):
    print(f"socket disconnected: {sid}")


@fastapi_app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@fastapi_app.get("/user")
def user_page(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    search: str = Query(""),
):
    page = paginate_query(
        "`user`",
        pageNum,
        pageSize,
        "id",
        [("username LIKE %s", search)],
    )
    return success(page)


@fastapi_app.get("/user/all")
def user_all():
    rows = fetch_all("SELECT * FROM `user`")
    return success([normalize_row(row) for row in rows])


@fastapi_app.get("/user/{username}")
def user_by_name(username: str):
    row = fetch_one("SELECT * FROM `user` WHERE username=%s", (username,))
    return success(normalize_row(row) if row else None)


@fastapi_app.post("/user/login")
def user_login(payload: UserPayload):
    user = fetch_one("SELECT * FROM `user` WHERE username=%s", (payload.username,))
    if not user:
        return error("用户名不存在！")
    if (payload.password or "") != (user.get("password") or ""):
        return error("密码错误！")
    return success(normalize_row(user))


@fastapi_app.post("/user/register")
def user_register(payload: UserPayload):
    exists = fetch_one("SELECT id FROM `user` WHERE username=%s", (payload.username,))
    if exists:
        return error("用户名重复")

    sql = (
        "INSERT INTO `user` (username, password, name, sex, role, email, time, tel, avatar) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    execute(
        sql,
        (
            payload.username,
            payload.password,
            "张三",
            "男",
            "common",
            "123@qq.com",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "1234567889",
            "https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif",
        ),
    )
    return success()


@fastapi_app.post("/user/update")
def user_update(payload: UserPayload):
    if payload.id is None:
        return error("缺少用户ID")
    update_record("user", model_to_dict(payload), payload.id)
    return success()


@fastapi_app.delete("/user/{record_id}")
def user_delete(record_id: int):
    execute("DELETE FROM `user` WHERE id=%s", (record_id,))
    return success()


@fastapi_app.post("/user")
def user_create(payload: UserPayload):
    data = model_to_dict(payload)
    data.pop("id", None)
    if not data.get("username"):
        return error("缺少用户名")
    insert_record("user", data)
    return success()


@fastapi_app.get("/imgRecords")
def img_records_page(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    search: str = Query(""),
    search1: str = Query(""),
    search3: str = Query(""),
    search2: str = Query(""),
):
    page = paginate_query(
        "imgrecords",
        pageNum,
        pageSize,
        "start_time",
        [
            ("username LIKE %s", search),
            ("kind LIKE %s", search1),
            ("label LIKE %s", search2),
            ("conf LIKE %s", search3),
        ],
    )
    return success(page)


@fastapi_app.get("/imgRecords/all")
def img_records_all():
    rows = fetch_all("SELECT * FROM imgrecords")
    return success([normalize_row(row) for row in rows])


@fastapi_app.get("/imgRecords/{record_id}")
def img_record_one(record_id: int):
    row = fetch_one("SELECT * FROM imgrecords WHERE id=%s", (record_id,))
    return success(normalize_row(row) if row else None)


@fastapi_app.delete("/imgRecords/{record_id}")
def img_record_delete(record_id: int):
    execute("DELETE FROM imgrecords WHERE id=%s", (record_id,))
    return success()


@fastapi_app.post("/imgRecords/update")
def img_record_update(payload: ImgRecordPayload):
    if payload.id is None:
        return error("缺少记录ID")
    update_record("imgrecords", model_to_dict(payload), payload.id)
    return success()


@fastapi_app.post("/imgRecords")
def img_record_create(payload: ImgRecordPayload):
    data = model_to_dict(payload)
    data.pop("id", None)
    insert_record("imgrecords", data)
    return success()


@fastapi_app.get("/imgRecords/statistics")
def img_statistics():
    rows = fetch_all("SELECT * FROM imgrecords")
    records = [normalize_row(row) for row in rows]

    label_count: Dict[str, int] = {}
    user_conf_sum: Dict[str, float] = {}
    user_conf_cnt: Dict[str, int] = {}
    user_predict_count: Dict[str, int] = {}
    time_consume_list: List[Dict[str, Any]] = []

    for row in records:
        label_list = safe_json_loads(row.get("label") or "[]")
        if isinstance(label_list, list):
            for label in label_list:
                if label:
                    label_count[label] = label_count.get(label, 0) + 1

        username = row.get("username") or ""
        if username:
            user_predict_count[username] = user_predict_count.get(username, 0) + 1

        conf_list = safe_json_loads(row.get("confidence") or "[]")
        if username and isinstance(conf_list, list) and conf_list:
            total = 0.0
            cnt = 0
            for conf in conf_list:
                try:
                    total += float(str(conf).replace("%", "").strip())
                    cnt += 1
                except Exception:
                    pass
            if cnt > 0:
                user_conf_sum[username] = user_conf_sum.get(username, 0.0) + (total / cnt)
                user_conf_cnt[username] = user_conf_cnt.get(username, 0) + 1

        all_time = str(row.get("allTime") or "")
        if "秒" in all_time:
            try:
                consume = float(all_time.replace("秒", "").strip())
            except Exception:
                consume = 0.0
            time_consume_list.append(
                {
                    "id": row.get("id"),
                    "username": username,
                    "label": row.get("label"),
                    "kind": row.get("kind"),
                    "consumeTime": consume,
                    "startTime": row.get("startTime"),
                }
            )

    user_avg_conf = {
        user: (user_conf_sum[user] / user_conf_cnt[user]) for user in user_conf_sum if user_conf_cnt.get(user, 0) > 0
    }

    return success(
        {
            "labelCount": label_count,
            "userAvgConf": user_avg_conf,
            "userPredictCount": user_predict_count,
            "timeConsumeList": time_consume_list,
        }
    )


@fastapi_app.get("/videoRecords")
def video_records_page(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    search: str = Query(""),
    search1: str = Query(""),
    search3: str = Query(""),
    search2: str = Query(""),
):
    page = paginate_query(
        "videorecords",
        pageNum,
        pageSize,
        "start_time",
        [
            ("username LIKE %s", search),
            ("kind LIKE %s", search1),
            ("weight LIKE %s", search2),
            ("conf LIKE %s", search3),
        ],
    )
    return success(page)


@fastapi_app.get("/videoRecords/all")
def video_records_all():
    rows = fetch_all("SELECT * FROM videorecords")
    return success([normalize_row(row) for row in rows])


@fastapi_app.get("/videoRecords/{record_id}")
def video_record_one(record_id: int):
    row = fetch_one("SELECT * FROM videorecords WHERE id=%s", (record_id,))
    return success(normalize_row(row) if row else None)


@fastapi_app.delete("/videoRecords/{record_id}")
def video_record_delete(record_id: int):
    execute("DELETE FROM videorecords WHERE id=%s", (record_id,))
    return success()


@fastapi_app.post("/videoRecords/update")
def video_record_update(payload: VideoRecordPayload):
    if payload.id is None:
        return error("缺少记录ID")
    update_record("videorecords", model_to_dict(payload), payload.id)
    return success()


@fastapi_app.post("/videoRecords")
def video_record_create(payload: VideoRecordPayload):
    data = model_to_dict(payload)
    data.pop("id", None)
    insert_record("videorecords", data)
    return success()


@fastapi_app.get("/cameraRecords")
def camera_records_page(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    search: str = Query(""),
    search1: str = Query(""),
    search3: str = Query(""),
    search2: str = Query(""),
):
    page = paginate_query(
        "camerarecords",
        pageNum,
        pageSize,
        "start_time",
        [
            ("username LIKE %s", search),
            ("kind LIKE %s", search1),
            ("weight LIKE %s", search2),
            ("conf LIKE %s", search3),
        ],
    )
    return success(page)


@fastapi_app.get("/cameraRecords/all")
def camera_records_all():
    rows = fetch_all("SELECT * FROM camerarecords")
    return success([normalize_row(row) for row in rows])


@fastapi_app.get("/cameraRecords/{record_id}")
def camera_record_one(record_id: int):
    row = fetch_one("SELECT * FROM camerarecords WHERE id=%s", (record_id,))
    return success(normalize_row(row) if row else None)


@fastapi_app.delete("/cameraRecords/{record_id}")
def camera_record_delete(record_id: int):
    execute("DELETE FROM camerarecords WHERE id=%s", (record_id,))
    return success()


@fastapi_app.post("/cameraRecords/update")
def camera_record_update(payload: CameraRecordPayload):
    if payload.id is None:
        return error("缺少记录ID")
    update_record("camerarecords", model_to_dict(payload), payload.id)
    return success()


@fastapi_app.post("/cameraRecords")
def camera_record_create(payload: CameraRecordPayload):
    data = model_to_dict(payload)
    data.pop("id", None)
    insert_record("camerarecords", data)
    return success()


@fastapi_app.post("/files/upload")
def file_upload(file: UploadFile = File(...)):
    file_name = save_uploaded_file(file)
    return success(build_file_url(file_name))


@fastapi_app.post("/files/editor/upload")
def file_editor_upload(file: UploadFile = File(...)):
    file_name = save_uploaded_file(file)
    file_url = build_file_url(file_name)
    return {"errno": 0, "data": [{"url": file_url}]}


@fastapi_app.get("/files/{flag}")
def file_download(flag: str):
    file_path = file_path_from_flag(flag)
    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path=file_path, filename=file_path.name, media_type="application/octet-stream")


@fastapi_app.get("/flask/file_names")
def flask_file_names():
    weight_items = [{"value": name, "label": name} for name in get_weight_names()]
    return success(json.dumps({"weight_items": weight_items}, ensure_ascii=False))


@fastapi_app.post("/predictImg")
def predict_img_raw(payload: PredictRequest):
    if not payload.inputImg:
        return {"status": 400, "message": "未提供图片链接"}
    if not payload.weight:
        return {"status": 400, "message": "未提供权重"}

    try:
        result = run_image_predict(payload.weight, payload.inputImg, payload.kind or "plants", float(payload.conf or 0.5))
        result.update(
            {
                "username": payload.username,
                "weight": payload.weight,
                "conf": payload.conf,
                "startTime": payload.startTime,
                "inputImg": payload.inputImg,
                "kind": payload.kind,
            }
        )
        return result
    except Exception as exc:
        return {"status": 400, "message": str(exc)}


@fastapi_app.post("/flask/predict")
def flask_predict(payload: PredictRequest):
    if not payload.inputImg:
        return error("未提供图片链接")
    if not payload.weight:
        return error("未提供权重")

    try:
        result = run_image_predict(payload.weight, payload.inputImg, payload.kind or "plants", float(payload.conf or 0.5))

        if result.get("status") == 400:
            return error(f"Error: {result.get('message')}")

        insert_record(
            "imgrecords",
            {
                "weight": payload.weight,
                "conf": payload.conf,
                "kind": payload.kind,
                "inputImg": payload.inputImg,
                "username": payload.username,
                "startTime": payload.startTime,
                "label": result.get("label", "[]"),
                "confidence": result.get("confidence", "[]"),
                "allTime": result.get("allTime", ""),
                "outImg": result.get("outImg", ""),
            },
        )

        return success(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        return error(f"Error: {exc}")


@fastapi_app.post("/suggest")
def suggest(payload: SuggestRequest):
    if not payload.result:
        return {"code": 400, "msg": "缺少名称参数", "data": None}

    start = time.time()
    text = make_suggestion(payload.result, payload.kind or "")
    return {
        "code": 0,
        "msg": "成功介绍",
        "data": {
            "suggestion": text,
            "generate_time": f"{(time.time() - start):.2f}秒",
        },
    }


@fastapi_app.get("/predictVideo")
def predict_video(
    request: Request,
    username: str = Query(""),
    weight: str = Query(""),
    conf: float = Query(0.5),
    startTime: str = Query(""),
    inputVideo: str = Query(""),
    kind: str = Query(""),
):
    if not inputVideo:
        raise HTTPException(status_code=400, detail="未提供视频地址")
    if not weight:
        raise HTTPException(status_code=400, detail="未提供模型")

    client_id = request.query_params.get("clientId")
    room = client_id or None

    temp_download = VIDEO_DIR / "download.mp4"
    temp_avi = VIDEO_DIR / "camera_output.avi"
    temp_mp4 = VIDEO_DIR / "output.mp4"

    for path in (temp_download, temp_avi, temp_mp4):
        path.unlink(missing_ok=True)

    download_file(inputVideo, temp_download)

    cap = cv2.VideoCapture(str(temp_download))
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="无法打开视频文件")

    fps = int(cap.get(cv2.CAP_PROP_FPS) or 20)
    frame_width, frame_height = 640, 480
    writer = cv2.VideoWriter(
        str(temp_avi),
        cv2.VideoWriter_fourcc(*"XVID"),
        fps,
        (frame_width, frame_height),
    )

    model_path = WEIGHTS_DIR / weight
    if not model_path.exists():
        cap.release()
        writer.release()
        raise HTTPException(status_code=400, detail=f"模型不存在: {weight}")

    model = YOLO(str(model_path))
    class_counter: Dict[str, int] = {}
    total_frames = 0

    emit_event("message", "开始处理视频...", room)

    def generate() -> Generator[bytes, None, None]:
        nonlocal total_frames
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                total_frames += 1
                frame = cv2.resize(frame, (frame_width, frame_height))
                results = model.predict(source=frame, conf=conf, show=False)

                for box in results[0].boxes:
                    cls_id = int(box.cls[0])
                    cls_name = model.names[cls_id]
                    class_counter[cls_name] = class_counter.get(cls_name, 0) + 1

                plotted = results[0].plot()
                writer.write(plotted)
                _, jpeg = cv2.imencode(".jpg", plotted)
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
        finally:
            cap.release()
            writer.release()
            cv2.destroyAllWindows()

            if class_counter:
                top_name, top_count = max(class_counter.items(), key=lambda x: x[1])
                top_name = str(top_name).replace("HUO", "火").replace("YAN", "烟")
            else:
                top_name, top_count = "未识别到任何类别", 0

            desc = make_suggestion(top_name, kind)
            emit_event("most_frequent_class", {"name": top_name, "count": top_count, "desc": desc}, room)
            emit_event("total_frames", total_frames, room)
            emit_event("message", "处理完成，正在保存！", room)

            for progress in convert_avi_to_mp4(temp_avi, temp_mp4):
                emit_event("progress", progress, room)

            out_url = upload_local_file(temp_mp4)
            insert_record(
                "videorecords",
                {
                    "username": username,
                    "weight": weight,
                    "conf": str(conf),
                    "startTime": startTime,
                    "inputVideo": inputVideo,
                    "kind": kind,
                    "outVideo": out_url,
                },
            )

            for path in (temp_download, temp_avi, temp_mp4):
                path.unlink(missing_ok=True)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@fastapi_app.get("/predictCamera")
def predict_camera(
    request: Request,
    username: str = Query(""),
    weight: str = Query(""),
    conf: float = Query(0.5),
    startTime: str = Query(""),
    kind: str = Query(""),
):
    global camera_recording

    client_id = request.query_params.get("clientId")
    room = client_id or None

    temp_avi = VIDEO_DIR / "camera_output.avi"
    temp_mp4 = VIDEO_DIR / "output.mp4"

    for path in (temp_avi, temp_mp4):
        path.unlink(missing_ok=True)

    model_path = WEIGHTS_DIR / weight
    if not model_path.exists():
        raise HTTPException(status_code=400, detail=f"模型不存在: {weight}")

    model = YOLO(str(model_path))
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    writer = cv2.VideoWriter(
        str(temp_avi),
        cv2.VideoWriter_fourcc(*"XVID"),
        20,
        (640, 480),
    )

    camera_recording = True
    emit_event("message", "正在加载，请稍等！", room)

    def generate() -> Generator[bytes, None, None]:
        nonlocal cap, writer
        try:
            while camera_recording:
                ret, frame = cap.read()
                if not ret:
                    break

                results = model.predict(source=frame, imgsz=640, conf=conf, show=False)
                plotted = results[0].plot()
                writer.write(plotted)

                _, jpeg = cv2.imencode(".jpg", plotted)
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
        finally:
            cap.release()
            writer.release()
            cv2.destroyAllWindows()

            emit_event("message", "处理完成，正在保存！", room)
            for progress in convert_avi_to_mp4(temp_avi, temp_mp4):
                emit_event("progress", progress, room)

            out_url = upload_local_file(temp_mp4)
            insert_record(
                "camerarecords",
                {
                    "username": username,
                    "weight": weight,
                    "conf": str(conf),
                    "startTime": startTime,
                    "kind": kind,
                    "outVideo": out_url,
                },
            )

            for path in (temp_avi, temp_mp4):
                path.unlink(missing_ok=True)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@fastapi_app.get("/stopCamera")
def stop_camera():
    global camera_recording
    camera_recording = False
    return {"status": 200, "message": "预测成功", "code": 0, "data": json.dumps({"weight_items": []}, ensure_ascii=False)}


app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=SERVER_PORT, reload=False)
