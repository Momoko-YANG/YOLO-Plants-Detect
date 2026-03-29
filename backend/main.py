import asyncio
import sys
from pathlib import Path

import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import DIST_DIR, SERVER_PORT
from backend.routers import camera_records, files, img_records, predict, users, video_records

fastapi_app = FastAPI(title="YOLO FastAPI Backend")
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ, auth):
    await sio.emit("message", {"data": "Connected to WebSocket server!"}, room=sid)


@sio.event
async def disconnect(sid):
    print(f"socket disconnected: {sid}")


@fastapi_app.on_event("startup")
async def on_startup() -> None:
    predict.init_predict_router(asyncio.get_running_loop(), sio)


@fastapi_app.get("/health")
def health():
    return {"status": "ok"}


@fastapi_app.get("/", include_in_schema=False)
def web_root():
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"msg": "Frontend dist not found"}


fastapi_app.include_router(users.router)
fastapi_app.include_router(img_records.router)
fastapi_app.include_router(video_records.router)
fastapi_app.include_router(camera_records.router)
fastapi_app.include_router(files.router)
fastapi_app.include_router(predict.router)

if (DIST_DIR / "assets").exists():
    fastapi_app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")


@fastapi_app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    candidate = DIST_DIR / full_path
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Not Found")


app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=SERVER_PORT, reload=False)
