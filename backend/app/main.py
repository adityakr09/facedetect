"""
FaceDetect API – main application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import engine
from app.db import models  # noqa: F401 – ensures models are registered
from app.api import feed, stream, roi, health


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup – Alembic handles DDL; nothing extra needed here.
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="FaceDetect API",
    version="1.0.0",
    description="Real-time face detection with ROI persistence.",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health.router, tags=["health"])
app.include_router(feed.router,   prefix="/api/v1", tags=["feed"])
app.include_router(stream.router, prefix="/api/v1", tags=["stream"])
app.include_router(roi.router,    prefix="/api/v1", tags=["roi"])
