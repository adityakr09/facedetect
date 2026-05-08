from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Session ───────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    client_ip: Optional[str] = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    started_at: datetime
    ended_at: Optional[datetime]
    client_ip: Optional[str]


# ── ROI ───────────────────────────────────────────────────────────────────────

class ROIResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    frame_id: int
    x: int
    y: int
    width: int
    height: int
    confidence: float
    detected_at: datetime


class FrameROIResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    frame_index: int
    captured_at: datetime
    face_detected: bool
    roi: Optional[ROIResponse] = None


class ROIListResponse(BaseModel):
    session_id: uuid.UUID
    total: int
    items: list[FrameROIResponse]


# ── Feed ──────────────────────────────────────────────────────────────────────

class FeedStartResponse(BaseModel):
    session_id: str
    stream_url: str
    roi_url: str
