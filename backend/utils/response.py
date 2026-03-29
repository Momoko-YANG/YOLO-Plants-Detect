from typing import Any, Dict


def success(data: Any = None) -> Dict[str, Any]:
    return {"code": "0", "msg": "成功", "data": data}


def error(msg: str, code: str = "-1") -> Dict[str, Any]:
    return {"code": code, "msg": msg, "data": None}
