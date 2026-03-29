from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from backend.config import FALLBACK_USERS
from backend.database.db import execute, fetch_all, fetch_one, insert_record, paginate_query, update_record
from backend.models.schemas import UserPayload
from backend.utils.converters import model_to_dict, normalize_row
from backend.utils.response import error, success

router = APIRouter()


def get_fallback_user(username: str) -> Optional[Dict[str, Any]]:
    for user in FALLBACK_USERS:
        if user["username"] == username:
            return dict(user)
    return None


def fallback_user_page(page_num: int, page_size: int, search: str) -> Dict[str, Any]:
    data = FALLBACK_USERS
    if search.strip():
        data = [u for u in data if search.strip() in str(u.get("username", ""))]
    total = len(data)
    start = max(page_num - 1, 0) * page_size
    end = start + page_size
    records = [normalize_row(u) for u in data[start:end]]
    pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "records": records,
        "total": total,
        "size": page_size,
        "current": page_num,
        "pages": pages,
    }


@router.get("/user")
def user_page(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    search: str = Query(""),
):
    page = paginate_query(
        "`user`", pageNum, pageSize, "id",
        [("username LIKE %s", search)],
    )
    if not page.get("records"):
        page = fallback_user_page(pageNum, pageSize, search)
    return success(page)


@router.get("/user/all")
def user_all():
    rows = fetch_all("SELECT * FROM `user`")
    if rows:
        return success([normalize_row(row) for row in rows])
    return success([normalize_row(u) for u in FALLBACK_USERS])


@router.get("/user/{username}")
def user_by_name(username: str):
    row = fetch_one("SELECT * FROM `user` WHERE username=%s", (username,))
    if row:
        return success(normalize_row(row))
    fb = get_fallback_user(username)
    return success(normalize_row(fb) if fb else None)


@router.post("/user/login")
def user_login(payload: UserPayload):
    user = fetch_one("SELECT * FROM `user` WHERE username=%s", (payload.username,))
    if user:
        if (payload.password or "") != (user.get("password") or ""):
            return error("密码错误！")
        return success(normalize_row(user))

    fb = get_fallback_user(payload.username or "")
    if not fb:
        return error("用户名不存在！")
    if (payload.password or "") != (fb.get("password") or ""):
        return error("密码错误！")
    return success(normalize_row(fb))


@router.post("/user/register")
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
            payload.username, payload.password, "张三", "男", "common",
            "123@qq.com", datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "1234567889",
            "https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif",
        ),
    )
    return success()


@router.post("/user/update")
def user_update(payload: UserPayload):
    if payload.id is None:
        return error("缺少用户ID")
    update_record("user", model_to_dict(payload), payload.id)
    return success()


@router.delete("/user/{record_id}")
def user_delete(record_id: int):
    execute("DELETE FROM `user` WHERE id=%s", (record_id,))
    return success()


@router.post("/user")
def user_create(payload: UserPayload):
    data = model_to_dict(payload)
    data.pop("id", None)
    if not data.get("username"):
        return error("缺少用户名")
    insert_record("user", data)
    return success()
