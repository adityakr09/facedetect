"""
WS /api/v1/stream/{session_id}
───────────────────────────────
Endpoint 2 – Serve annotated video feed.

Streams annotated JPEG frames (as binary WebSocket messages) to the
React frontend. Each message is a raw JPEG that the browser renders
as a video-like sequence.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.session_store import session_store

logger = logging.getLogger(__name__)
router = APIRouter()

_SEND_TIMEOUT = 5.0  # seconds to wait before giving up on a slow client


@router.websocket("/stream/{session_id}")
async def stream_frames(websocket: WebSocket, session_id: str) -> None:
    """
    Endpoint 2 – WebSocket that pushes annotated JPEG frames to the client.
    """
    q = session_store.get(session_id)
    if q is None:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()
    logger.info("Stream client connected: %s", session_id)

    try:
        while True:
            # Wait for the next annotated frame (or sentinel None)
            try:
                frame: bytes | None = await asyncio.wait_for(q.get(), timeout=30.0)
            except asyncio.TimeoutError:
                # No frame received in 30 s – send a ping to keep the WS alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
                continue

            if frame is None:
                # Sentinel – session ended
                logger.info("Session ended, closing stream: %s", session_id)
                break

            try:
                await asyncio.wait_for(
                    websocket.send_bytes(frame), timeout=_SEND_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning("Slow client; dropping frame: %s", session_id)
            except Exception as exc:
                logger.warning("Send error (%s): %s", session_id, exc)
                break

    except WebSocketDisconnect:
        logger.info("Stream client disconnected: %s", session_id)
    finally:
        logger.info("Stream handler exiting: %s", session_id)
