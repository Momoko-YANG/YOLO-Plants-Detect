import json
from typing import Any, Dict, List

from fastapi import APIRouter, Query

from backend.database.db import (
    execute,
    fetch_all,
    fetch_one,
    insert_record,
    paginate_query,
    update_record,
)
from backend.models.schemas import ImgRecordPayload
from backend.utils.converters import model_to_dict, normalize_row
from backend.utils.response import error, success

router = APIRouter()


def safe_json_loads(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return []


@router.get("/imgRecords")
def img_records_page(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    search: str = Query(""),
    search1: str = Query(""),
    search3: str = Query(""),
    search2: str = Query(""),
):
    page = paginate_query(
        "imgrecords", pageNum, pageSize, "start_time",
        [
            ("username LIKE %s", search),
            ("kind LIKE %s", search1),
            ("label LIKE %s", search2),
            ("conf LIKE %s", search3),
        ],
    )
    return success(page)


@router.get("/imgRecords/all")
def img_records_all():
    rows = fetch_all("SELECT * FROM imgrecords")
    return success([normalize_row(row) for row in rows])


@router.get("/imgRecords/statistics")
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
            time_consume_list.append({
                "id": row.get("id"),
                "username": username,
                "label": row.get("label"),
                "kind": row.get("kind"),
                "consumeTime": consume,
                "startTime": row.get("startTime"),
            })

    user_avg_conf = {
        user: (user_conf_sum[user] / user_conf_cnt[user])
        for user in user_conf_sum
        if user_conf_cnt.get(user, 0) > 0
    }

    return success({
        "labelCount": label_count,
        "userAvgConf": user_avg_conf,
        "userPredictCount": user_predict_count,
        "timeConsumeList": time_consume_list,
    })


@router.get("/imgRecords/{record_id}")
def img_record_one(record_id: int):
    row = fetch_one("SELECT * FROM imgrecords WHERE id=%s", (record_id,))
    return success(normalize_row(row) if row else None)


@router.delete("/imgRecords/{record_id}")
def img_record_delete(record_id: int):
    execute("DELETE FROM imgrecords WHERE id=%s", (record_id,))
    return success()


@router.post("/imgRecords/update")
def img_record_update(payload: ImgRecordPayload):
    if payload.id is None:
        return error("缺少记录ID")
    update_record("imgrecords", model_to_dict(payload), payload.id)
    return success()


@router.post("/imgRecords")
def img_record_create(payload: ImgRecordPayload):
    data = model_to_dict(payload)
    data.pop("id", None)
    insert_record("imgrecords", data)
    return success()
