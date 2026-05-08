"""
SQLAlchemy ORM models.

Schema
──────
sessions        – one row per video streaming session
frames          – one row per processed video frame
rois            – one row per detected face bounding box (one per frame)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    UUID,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    frames: Mapped[list["Frame"]] = relationship(back_populates="session")


class Frame(Base):
    __tablename__ = "frames"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    frame_index: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    face_detected: Mapped[bool] = mapped_column(default=False)

    session: Mapped["Session"] = relationship(back_populates="frames")
    roi: Mapped["ROI | None"] = relationship(back_populates="frame", uselist=False)


class ROI(Base):
    """Axis-aligned minimal bounding box for one detected face."""

    __tablename__ = "rois"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    frame_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("frames.id", ondelete="CASCADE"), unique=True, index=True
    )
    # Pixel coordinates of the bounding box (top-left origin)
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    # Confidence score [0.0 – 1.0] reported by the detector
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    frame: Mapped["Frame"] = relationship(back_populates="roi")
