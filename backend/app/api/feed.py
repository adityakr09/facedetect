"""
POST /api/v1/feed/{session_id}
──────────────────────────────
Accepts a raw JPEG frame, runs face detection, persists ROI data, and
enqueues the annotated JPEG for the stream WebSocket to consume.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Frame, ROI, Session
from app.models.schemas import FeedStartResponse
from app.services.detection import process_frame
from app.services.session_store import session_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/feed/start",
    response_model=FeedStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new streaming session",
)
async def start_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FeedStartResponse:
    """Create a session record and return the session_id + endpoint URLs."""
    session_id = session_store.generate_id()
    session_store.create(session_id)

    client_ip = request.client.host if request.client else None
    db_session = Session(id=session_id, client_ip=client_ip)  # type: ignore[arg-type]
    db.add(db_session)
    await db.flush()

    base = str(request.base_url).rstrip("/")
    return FeedStartResponse(
        session_id=session_id,
        stream_url=f"{base}/api/v1/stream/{session_id}",
        roi_url=f"{base}/api/v1/roi/{session_id}",
    )


@router.post(
    "/feed/{session_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Push a JPEG frame into an active session",
)
async def push_frame(
    session_id: str,
    frame_file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Endpoint 1 – Receive video feed.

    Accepts a JPEG uploaded as multipart/form-data field `frame_file`.
    Processes the frame, stores ROI in the database, and pushes the
    annotated JPEG to the session queue for WebSocket streaming.
    """
    q = session_store.get(session_id)
    if q is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or already closed.",
        )

    if frame_file.content_type not in ("image/jpeg", "image/jpg"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only image/jpeg is accepted.",
        )

    raw = await frame_file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty frame."
        )

    # Run detection (CPU-bound) in a thread so we don't block the event loop
    try:
        result = await asyncio.get_running_loop().run_in_executor(
            None, process_frame, raw
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # Persist frame metadata
    from sqlalchemy import select
    stmt = select(Session).where(Session.id == session_id)  # type: ignore[arg-type]
    db_session = (await db.execute(stmt)).scalar_one_or_none()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not in DB.")

    # Count existing frames for this session to get frame_index
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(Frame).where(Frame.session_id == session_id)  # type: ignore[arg-type]
    frame_index = (await db.execute(count_stmt)).scalar() or 0

    frame = Frame(
        session_id=session_id,  # type: ignore[arg-type]
        frame_index=frame_index,
        width=result.frame_width,
        height=result.frame_height,
        face_detected=result.bbox is not None,
    )
    db.add(frame)
    await db.flush()  # populate frame.id

    if result.bbox:
        roi = ROI(
            frame_id=frame.id,
            x=result.bbox.x,
            y=result.bbox.y,
            width=result.bbox.width,
            height=result.bbox.height,
            confidence=result.bbox.confidence,
        )
        db.add(roi)

    # Push annotated frame to the queue (drop oldest if full to avoid stalling)
    try:
        q.put_nowait(result.annotated_jpeg)
    except asyncio.QueueFull:
        try:
            q.get_nowait()  # drop oldest
        except asyncio.QueueEmpty:
            pass
        q.put_nowait(result.annotated_jpeg)

    return {
        "frame_index": frame_index,
        "face_detected": result.bbox is not None,
        "roi": (
            {
                "x": result.bbox.x,
                "y": result.bbox.y,
                "width": result.bbox.width,
                "height": result.bbox.height,
            }
            if result.bbox
            else None
        ),
    }


@router.post(
    "/feed/{session_id}/stop",
    summary="End a streaming session",
)
async def stop_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from sqlalchemy import select, update
    from datetime import datetime, timezone

    q = session_store.get(session_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    session_store.close(session_id)

    await db.execute(
        update(Session)
        .where(Session.id == session_id)  # type: ignore[arg-type]
        .values(ended_at=datetime.now(timezone.utc))
    )

    return {"session_id": session_id, "status": "closed"}
