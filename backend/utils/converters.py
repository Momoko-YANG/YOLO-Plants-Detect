from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


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


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)
