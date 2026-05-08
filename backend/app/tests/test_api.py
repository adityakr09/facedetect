"""
Unit and integration tests for the FaceDetect API.
Run with:  pytest -v
"""

from __future__ import annotations

import io
import struct
import zlib
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_jpeg(width: int = 320, height: int = 240, color=(128, 0, 0)) -> bytes:
    """Create a minimal solid-colour JPEG in memory."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ── Detection service tests ───────────────────────────────────────────────────


class TestProcessFrame:
    def test_returns_result_with_no_face(self):
        from app.services.detection import process_frame

        jpeg = make_jpeg()
        with patch("app.services.detection.face_recognition.face_locations", return_value=[]):
            result = process_frame(jpeg)

        assert result.bbox is None
        assert result.frame_width == 320
        assert result.frame_height == 240
        assert len(result.annotated_jpeg) > 0

    def test_returns_bbox_when_face_detected(self):
        from app.services.detection import process_frame

        jpeg = make_jpeg(640, 480)
        fake_locations = [(50, 200, 200, 100)]  # top, right, bottom, left
        with patch("app.services.detection.face_recognition.face_locations", return_value=fake_locations):
            result = process_frame(jpeg)

        assert result.bbox is not None
        assert result.bbox.x == 100
        assert result.bbox.y == 50
        assert result.bbox.width == 100   # right - left
        assert result.bbox.height == 150  # bottom - top

    def test_invalid_bytes_raises_value_error(self):
        from app.services.detection import process_frame

        with pytest.raises(ValueError, match="Invalid image"):
            process_frame(b"not-an-image")

    def test_annotated_jpeg_is_valid(self):
        from app.services.detection import process_frame

        jpeg = make_jpeg()
        with patch("app.services.detection.face_recognition.face_locations", return_value=[]):
            result = process_frame(jpeg)

        # Verify we can re-open the annotated JPEG
        img = Image.open(io.BytesIO(result.annotated_jpeg))
        assert img.format == "JPEG"

    def test_roi_clamped_to_image_bounds(self):
        from app.services.detection import process_frame

        jpeg = make_jpeg(100, 100)
        # Location extends well outside the image
        fake_locations = [(0, 500, 500, 0)]
        with patch("app.services.detection.face_recognition.face_locations", return_value=fake_locations):
            result = process_frame(jpeg)

        assert result.bbox is not None
        assert result.bbox.x >= 0
        assert result.bbox.y >= 0
        assert result.bbox.x + result.bbox.width <= 100
        assert result.bbox.y + result.bbox.height <= 100


# ── BoundingBox tests ─────────────────────────────────────────────────────────


class TestBoundingBox:
    def test_right_and_bottom(self):
        from app.services.detection import BoundingBox

        bb = BoundingBox(x=10, y=20, width=50, height=80)
        assert bb.right == 60
        assert bb.bottom == 100


# ── Session store tests ───────────────────────────────────────────────────────


class TestSessionStore:
    def test_create_and_get(self):
        from app.services.session_store import SessionStore

        store = SessionStore()
        sid = store.generate_id()
        q = store.create(sid)
        assert store.get(sid) is q

    def test_get_missing_returns_none(self):
        from app.services.session_store import SessionStore

        store = SessionStore()
        assert store.get("nonexistent") is None

    def test_close_sends_sentinel(self):
        import asyncio
        from app.services.session_store import SessionStore

        store = SessionStore()
        sid = store.generate_id()
        store.create(sid)
        store.close(sid)

        # After close the session should be gone
        assert store.get(sid) is None


# ── API endpoint smoke tests (no DB) ─────────────────────────────────────────


@pytest.fixture
def client():
    """TestClient with DB dependency overridden to a no-op async session."""
    from app.main import app
    from app.db.session import get_db

    async def _fake_db():
        mock_session = MagicMock()
        mock_session.flush = MagicMock(return_value=_noop())
        mock_session.add = MagicMock()
        mock_session.execute = MagicMock(return_value=_exec_result())
        yield mock_session

    async def _noop():
        pass

    def _exec_result():
        r = MagicMock()
        r.scalar_one_or_none.return_value = MagicMock()
        r.scalar.return_value = 0
        return r

    app.dependency_overrides[get_db] = _fake_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_push_frame_unknown_session(client):
    jpeg = make_jpeg()
    r = client.post(
        "/api/v1/feed/nonexistent-session-id",
        files={"frame_file": ("frame.jpg", jpeg, "image/jpeg")},
    )
    assert r.status_code == 404


def test_push_frame_wrong_content_type(client):
    from app.services.session_store import session_store

    sid = session_store.generate_id()
    session_store.create(sid)
    try:
        r = client.post(
            f"/api/v1/feed/{sid}",
            files={"frame_file": ("frame.png", b"data", "image/png")},
        )
        assert r.status_code == 415
    finally:
        session_store.close(sid)
