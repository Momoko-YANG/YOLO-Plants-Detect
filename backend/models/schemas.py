from typing import Optional

from pydantic import BaseModel


class PredictRequest(BaseModel):
    startTime: Optional[str] = ""
    weight: Optional[str] = ""
    username: Optional[str] = ""
    inputImg: Optional[str] = ""
    kind: Optional[str] = ""
    conf: Optional[str] = ""


class SuggestRequest(BaseModel):
    result: Optional[str] = ""
    kind: Optional[str] = ""


class UserPayload(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = ""
    password: Optional[str] = ""
    name: Optional[str] = ""
    sex: Optional[str] = ""
    email: Optional[str] = ""
    tel: Optional[str] = ""
    role: Optional[str] = ""
    avatar: Optional[str] = ""
    time: Optional[str] = None


class ImgRecordPayload(BaseModel):
    id: Optional[int] = None
    weight: Optional[str] = ""
    inputImg: Optional[str] = ""
    outImg: Optional[str] = ""
    confidence: Optional[str] = ""
    allTime: Optional[str] = ""
    conf: Optional[str] = ""
    label: Optional[str] = ""
    username: Optional[str] = ""
    kind: Optional[str] = ""
    startTime: Optional[str] = ""


class VideoRecordPayload(BaseModel):
    id: Optional[int] = None
    weight: Optional[str] = ""
    inputVideo: Optional[str] = ""
    outVideo: Optional[str] = ""
    conf: Optional[str] = ""
    username: Optional[str] = ""
    kind: Optional[str] = ""
    startTime: Optional[str] = ""


class CameraRecordPayload(BaseModel):
    id: Optional[int] = None
    weight: Optional[str] = ""
    outVideo: Optional[str] = ""
    conf: Optional[str] = ""
    username: Optional[str] = ""
    kind: Optional[str] = ""
    startTime: Optional[str] = ""
