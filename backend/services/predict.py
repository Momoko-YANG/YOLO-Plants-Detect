import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Generator, List

import cv2
import requests

from backend.config import (
    RESULT_IMG_PATH,
    RUNS_DIR,
    SERVER_HOST,
    SERVER_PORT,
    UPLOADS_DIR,
    WEIGHTS_DIR,
)


def download_file(url: str, save_path: Path) -> None:
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with save_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def upload_local_file(local_path: Path) -> str:
    file_name = f"{uuid.uuid4().hex}_{local_path.name}"
    target = UPLOADS_DIR / file_name
    target.write_bytes(local_path.read_bytes())
    return f"http://{SERVER_HOST}:{SERVER_PORT}/files/{file_name}"


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


LABELS_MAP = {
    "plants": [
        "苹果黑星病叶", "苹果叶片", "苹果锈病叶", "甜椒叶片", "甜椒叶斑病叶",
        "蓝莓叶片", "樱桃叶片", "玉米灰斑病叶", "玉米叶枯病叶", "玉米锈病叶",
        "桃树叶片", "马铃薯叶片", "马铃薯早疫病叶", "马铃薯晚疫病叶", "覆盆子叶片",
        "大豆叶片（拼写变体）", "大豆叶片", "南瓜白粉病叶", "草莓叶片",
        "番茄早疫病叶", "番茄斑枯病叶", "番茄叶片", "番茄细菌性斑点病叶",
        "番茄晚疫病叶", "番茄花叶病毒病叶", "番茄黄化病毒病叶", "番茄霉病叶",
        "番茄二斑叶螨危害叶", "葡萄叶片", "葡萄黑腐病叶",
    ]
}


def run_image_predict(weight: str, img_url: str, kind: str, conf: float) -> Dict[str, Any]:
    from ultralytics import YOLO

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

    labels_dict = LABELS_MAP.get(kind, LABELS_MAP["plants"])
    output: Dict[str, Any] = {
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
