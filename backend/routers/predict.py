import asyncio
import json
from typing import Any, Dict, Generator, Optional

import cv2
import socketio
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from backend.config import UPLOADS_DIR, VIDEO_DIR, WEIGHTS_DIR
from backend.database.db import insert_record
from backend.models.schemas import PredictRequest, SuggestRequest
from backend.services.predict import (
    convert_avi_to_mp4,
    download_file,
    run_image_predict,
    upload_local_file,
)
from backend.services.suggestion import make_suggestion
from backend.utils.response import error, success

router = APIRouter()

camera_recording = False
main_loop: Optional[asyncio.AbstractEventLoop] = None
sio: Optional[socketio.AsyncServer] = None


def init_predict_router(loop: asyncio.AbstractEventLoop, sio_server: socketio.AsyncServer) -> None:
    global main_loop, sio
    main_loop = loop
    sio = sio_server


def emit_event(event: str, payload: Any, room: Optional[str] = None) -> None:
    if main_loop and main_loop.is_running() and sio:
        future = asyncio.run_coroutine_threadsafe(
            sio.emit(event, {"data": payload}, room=room),
            main_loop,
        )
        try:
            future.result(timeout=5)
        except Exception as exc:
            print(f"socket emit error: {exc}")


import time


@router.post("/predictImg")
def predict_img_raw(payload: PredictRequest):
    if not payload.inputImg:
        return {"status": 400, "message": "未提供图片链接"}
    if not payload.weight:
        return {"status": 400, "message": "未提供权重"}

    try:
        result = run_image_predict(
            payload.weight, payload.inputImg,
            payload.kind or "plants", float(payload.conf or 0.5),
        )
        result.update({
            "username": payload.username,
            "weight": payload.weight,
            "conf": payload.conf,
            "startTime": payload.startTime,
            "inputImg": payload.inputImg,
            "kind": payload.kind,
        })
        return result
    except Exception as exc:
        return {"status": 400, "message": str(exc)}


@router.post("/flask/predict")
def flask_predict(payload: PredictRequest):
    if not payload.inputImg:
        return error("未提供图片链接")
    if not payload.weight:
        return error("未提供权重")

    try:
        result = run_image_predict(
            payload.weight, payload.inputImg,
            payload.kind or "plants", float(payload.conf or 0.5),
        )
        if result.get("status") == 400:
            return error(f"Error: {result.get('message')}")

        insert_record("imgrecords", {
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
        })
        return success(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        return error(f"Error: {exc}")


@router.post("/suggest")
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


@router.get("/predictVideo")
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
        str(temp_avi), cv2.VideoWriter_fourcc(*"XVID"), fps, (frame_width, frame_height),
    )

    from ultralytics import YOLO

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
            insert_record("videorecords", {
                "username": username, "weight": weight, "conf": str(conf),
                "startTime": startTime, "inputVideo": inputVideo,
                "kind": kind, "outVideo": out_url,
            })

            for path in (temp_download, temp_avi, temp_mp4):
                path.unlink(missing_ok=True)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/predictCamera")
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

    from ultralytics import YOLO

    model_path = WEIGHTS_DIR / weight
    if not model_path.exists():
        raise HTTPException(status_code=400, detail=f"模型不存在: {weight}")

    model = YOLO(str(model_path))
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    writer = cv2.VideoWriter(
        str(temp_avi), cv2.VideoWriter_fourcc(*"XVID"), 20, (640, 480),
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
            insert_record("camerarecords", {
                "username": username, "weight": weight, "conf": str(conf),
                "startTime": startTime, "kind": kind, "outVideo": out_url,
            })

            for path in (temp_avi, temp_mp4):
                path.unlink(missing_ok=True)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/stopCamera")
def stop_camera():
    global camera_recording
    camera_recording = False
    return {"status": 200, "message": "预测成功", "code": 0, "data": json.dumps({"weight_items": []}, ensure_ascii=False)}
