from typing import Any, Dict, List, Optional

import pymysql

from backend.config import DB_CONFIG
from backend.utils.converters import camel_to_snake, normalize_row


def get_conn() -> pymysql.Connection:
    return pymysql.connect(**DB_CONFIG)


def fetch_one(sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchone()
        finally:
            conn.close()
    except Exception as exc:
        print(f"DB fetch_one error: {exc}")
        return None


def fetch_all(sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchall()
        finally:
            conn.close()
    except Exception as exc:
        print(f"DB fetch_all error: {exc}")
        return []


def execute(sql: str, params: Optional[tuple] = None) -> int:
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cursor:
                affected = cursor.execute(sql, params or ())
                conn.commit()
                return affected
        finally:
            conn.close()
    except Exception as exc:
        print(f"DB execute error: {exc}")
        return 0


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
