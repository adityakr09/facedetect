"""
In-memory session store.

Maps session_id → asyncio.Queue of annotated JPEG bytes so the
/stream WebSocket can pull frames produced by /feed.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict

logger = logging.getLogger(__name__)

_QUEUE_MAXSIZE = 30  # ~1 second of buffer at 30 fps


class SessionStore:
    def __init__(self) -> None:
        self._queues: Dict[str, asyncio.Queue[bytes | None]] = {}

    def create(self, session_id: str) -> asyncio.Queue[bytes | None]:
        q: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
        self._queues[session_id] = q
        logger.info("Session created: %s", session_id)
        return q

    def get(self, session_id: str) -> asyncio.Queue[bytes | None] | None:
        return self._queues.get(session_id)

    def close(self, session_id: str) -> None:
        q = self._queues.pop(session_id, None)
        if q is not None:
            # Sentinel – signals the consumer to stop
            try:
                q.put_nowait(None)
            except asyncio.QueueFull:
                pass
            logger.info("Session closed: %s", session_id)

    def generate_id(self) -> str:
        return str(uuid.uuid4())


# Application-level singleton
session_store = SessionStore()
