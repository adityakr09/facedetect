from __future__ import annotations
import io
import logging
from dataclasses import dataclass
from typing import Optional
import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw
from app.core.config import settings

logger = logging.getLogger(__name__)

_detector = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)

@dataclass(frozen=True, slots=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    confidence: float = 1.0

    @property
    def right(self): return self.x + self.width
    @property
    def bottom(self): return self.y + self.height

@dataclass(frozen=True, slots=True)
class DetectionResult:
    bbox: Optional[BoundingBox]
    frame_width: int
    frame_height: int
    annotated_jpeg: bytes

def _draw_roi(img, bbox):
    annotated = img.copy()
    draw = ImageDraw.Draw(annotated)
    draw.rectangle([bbox.x-3, bbox.y-3, bbox.right+3, bbox.bottom+3], outline=(0,0,0), width=1)
    draw.rectangle([bbox.x, bbox.y, bbox.right, bbox.bottom], outline=(57,255,20), width=3)
    label = f"Face {bbox.confidence:.0%}"
    lx, ly = bbox.x, max(0, bbox.y-22)
    draw.rectangle([lx, ly, lx+len(label)*7+4, ly+18], fill=(57,255,20))
    draw.text((lx+2, ly+2), label, fill=(0,0,0))
    return annotated

def process_frame(jpeg_bytes: bytes) -> DetectionResult:
    try:
        img = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Invalid image data: {exc}") from exc
    orig_w, orig_h = img.size
    results = _detector.process(np.asarray(img))
    bbox = None
    if results.detections:
        det = results.detections[0]
        rel = det.location_data.relative_bounding_box
        x = max(0, int(rel.xmin * orig_w))
        y = max(0, int(rel.ymin * orig_h))
        w = min(int(rel.width * orig_w), orig_w - x)
        h = min(int(rel.height * orig_h), orig_h - y)
        bbox = BoundingBox(x=x, y=y, width=w, height=h, confidence=det.score[0])
    annotated = _draw_roi(img, bbox) if bbox else img
    buf = io.BytesIO()
    annotated.save(buf, format="JPEG", quality=settings.stream_jpeg_quality, optimize=True)
    return DetectionResult(bbox=bbox, frame_width=orig_w, frame_height=orig_h, annotated_jpeg=buf.getvalue())