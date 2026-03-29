from fastapi import APIRouter, Query

from backend.database.db import (
    execute,
    fetch_all,
    fetch_one,
    insert_record,
    paginate_query,
    update_record,
)
from backend.models.schemas import VideoRecordPayload
from backend.utils.converters import model_to_dict, normalize_row
from backend.utils.response import error, success

router = APIRouter()


@router.get("/videoRecords")
def video_records_page(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    search: str = Query(""),
    search1: str = Query(""),
    search3: str = Query(""),
    search2: str = Query(""),
):
    page = paginate_query(
        "videorecords", pageNum, pageSize, "start_time",
        [
            ("username LIKE %s", search),
            ("kind LIKE %s", search1),
            ("weight LIKE %s", search2),
            ("conf LIKE %s", search3),
        ],
    )
    return success(page)


@router.get("/videoRecords/all")
def video_records_all():
    rows = fetch_all("SELECT * FROM videorecords")
    return success([normalize_row(row) for row in rows])


@router.get("/videoRecords/{record_id}")
def video_record_one(record_id: int):
    row = fetch_one("SELECT * FROM videorecords WHERE id=%s", (record_id,))
    return success(normalize_row(row) if row else None)


@router.delete("/videoRecords/{record_id}")
def video_record_delete(record_id: int):
    execute("DELETE FROM videorecords WHERE id=%s", (record_id,))
    return success()


@router.post("/videoRecords/update")
def video_record_update(payload: VideoRecordPayload):
    if payload.id is None:
        return error("缺少记录ID")
    update_record("videorecords", model_to_dict(payload), payload.id)
    return success()


@router.post("/videoRecords")
def video_record_create(payload: VideoRecordPayload):
    data = model_to_dict(payload)
    data.pop("id", None)
    insert_record("videorecords", data)
    return success()
