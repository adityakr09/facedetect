"""
GET /api/v1/roi/{session_id}
────────────────────────────
Endpoint 3 – Serve ROI data.

Returns paginated ROI records (bounding boxes) for a given session,
ordered by frame_index ascending.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import Frame, Session, ROI
from app.models.schemas import ROIListResponse, FrameROIResponse, ROIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/roi/{session_id}",
    response_model=ROIListResponse,
    summary="Retrieve ROI data for a session",
)
async def get_roi(
    session_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Number of frames to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max frames to return"),
    db: AsyncSession = Depends(get_db),
) -> ROIListResponse:
    """
    Endpoint 3 – Returns frame + ROI data for the given session.

    Supports pagination via `skip` and `limit` query parameters.
    """
    # Verify session exists
    session_stmt = select(Session).where(Session.id == session_id)
    db_session = (await db.execute(session_stmt)).scalar_one_or_none()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Total frame count
    count_stmt = select(func.count()).select_from(Frame).where(
        Frame.session_id == session_id
    )
    total: int = (await db.execute(count_stmt)).scalar() or 0

    # Fetch frames with their ROIs eagerly loaded
    frames_stmt = (
        select(Frame)
        .where(Frame.session_id == session_id)
        .options(selectinload(Frame.roi))
        .order_by(Frame.frame_index)
        .offset(skip)
        .limit(limit)
    )
    frames = (await db.execute(frames_stmt)).scalars().all()

    items: list[FrameROIResponse] = []
    for f in frames:
        roi_resp: ROIResponse | None = None
        if f.roi:
            roi_resp = ROIResponse.model_validate(f.roi)
        items.append(
            FrameROIResponse(
                frame_index=f.frame_index,
                captured_at=f.captured_at,
                face_detected=f.face_detected,
                roi=roi_resp,
            )
        )

    return ROIListResponse(session_id=session_id, total=total, items=items)


@router.get(
    "/roi/{session_id}/latest",
    response_model=FrameROIResponse | None,
    summary="Get the most recent frame ROI for a session",
)
async def get_latest_roi(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FrameROIResponse | None:
    """Returns the ROI from the most recently processed frame."""
    stmt = (
        select(Frame)
        .where(Frame.session_id == session_id)
        .options(selectinload(Frame.roi))
        .order_by(Frame.frame_index.desc())
        .limit(1)
    )
    frame = (await db.execute(stmt)).scalar_one_or_none()
    if frame is None:
        return None

    roi_resp: ROIResponse | None = None
    if frame.roi:
        roi_resp = ROIResponse.model_validate(frame.roi)

    return FrameROIResponse(
        frame_index=frame.frame_index,
        captured_at=frame.captured_at,
        face_detected=frame.face_detected,
        roi=roi_resp,
    )
