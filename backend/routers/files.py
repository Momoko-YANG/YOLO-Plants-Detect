import json
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.config import SERVER_HOST, SERVER_PORT, UPLOADS_DIR, WEIGHTS_DIR
from backend.services.predict import get_weight_names
from backend.utils.response import success

router = APIRouter()


def save_uploaded_file(upload_file: UploadFile) -> str:
    safe_name = os.path.basename(upload_file.filename or "upload.bin")
    file_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = UPLOADS_DIR / file_name
    with file_path.open("wb") as f:
        f.write(upload_file.file.read())
    return file_name


def build_file_url(file_name: str) -> str:
    return f"http://{SERVER_HOST}:{SERVER_PORT}/files/{file_name}"


def file_path_from_flag(flag: str) -> Optional[Path]:
    direct_path = UPLOADS_DIR / flag
    if direct_path.exists():
        return direct_path
    for item in UPLOADS_DIR.iterdir():
        if item.is_file() and flag in item.name:
            return item
    return None


@router.post("/files/upload")
def file_upload(file: UploadFile = File(...)):
    file_name = save_uploaded_file(file)
    return success(build_file_url(file_name))


@router.post("/files/editor/upload")
def file_editor_upload(file: UploadFile = File(...)):
    file_name = save_uploaded_file(file)
    file_url = build_file_url(file_name)
    return {"errno": 0, "data": [{"url": file_url}]}


@router.get("/files/{flag}")
def file_download(flag: str):
    file_path = file_path_from_flag(flag)
    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在")
    from fastapi.responses import FileResponse
    return FileResponse(path=file_path, filename=file_path.name, media_type="application/octet-stream")


@router.get("/flask/file_names")
def flask_file_names():
    weight_items = [{"value": name, "label": name} for name in get_weight_names()]
    return success(json.dumps({"weight_items": weight_items}, ensure_ascii=False))
