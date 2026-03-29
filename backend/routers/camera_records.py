from fastapi import APIRouter, Query

from backend.database.db import (
    execute,
    fetch_all,
    fetch_one,
    insert_record,
    paginate_query,
    update_record,
)
from backend.models.schemas import CameraRecordPayload
from backend.utils.converters import model_to_dict, normalize_row
from backend.utils.response import error, success

router = APIRouter()


@router.get("/cameraRecords")
def camera_records_page(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    search: str = Query(""),
    search1: str = Query(""),
    search3: str = Query(""),
    search2: str = Query(""),
):
    page = paginate_query(
        "camerarecords", pageNum, pageSize, "start_time",
        [
            ("username LIKE %s", search),
            ("kind LIKE %s", search1),
            ("weight LIKE %s", search2),
            ("conf LIKE %s", search3),
        ],
    )
    return success(page)


@router.get("/cameraRecords/all")
def camera_records_all():
    rows = fetch_all("SELECT * FROM camerarecords")
    return success([normalize_row(row) for row in rows])


@router.get("/cameraRecords/{record_id}")
def camera_record_one(record_id: int):
    row = fetch_one("SELECT * FROM camerarecords WHERE id=%s", (record_id,))
    return success(normalize_row(row) if row else None)


@router.delete("/cameraRecords/{record_id}")
def camera_record_delete(record_id: int):
    execute("DELETE FROM camerarecords WHERE id=%s", (record_id,))
    return success()


@router.post("/cameraRecords/update")
def camera_record_update(payload: CameraRecordPayload):
    if payload.id is None:
        return error("缺少记录ID")
    update_record("camerarecords", model_to_dict(payload), payload.id)
    return success()


@router.post("/cameraRecords")
def camera_record_create(payload: CameraRecordPayload):
    data = model_to_dict(payload)
    data.pop("id", None)
    insert_record("camerarecords", data)
    return success()
