<div align="center">

# 🎯 FACEDETECT
### Real-Time Face Detection & Video Streaming System

![Demo](../Facedetection_Demo.png)

<br/>

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Face_Detection-FF6F00?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

> A fully containerised, production-ready system that accepts a live webcam feed, detects faces in real-time using **MediaPipe** (no OpenCV), draws axis-aligned bounding boxes with **Pillow**, persists ROI data to **PostgreSQL**, and streams annotated frames to a **React** frontend over **WebSocket**.

**94.9% detection rate · 10 FPS · <50ms annotation latency**

</div>

---

## ⚡ Run in 5 Minutes

````bash
# 1. Clone
git clone https://github.com/adityakr09/facedetect.git
cd facedetect

# 2. Configure
cp .env.example .env          # edit secrets if needed

# 3. Launch
docker compose up --build     # first build ~10 min (mediapipe compiles)

# 4. Open
# http://localhost → Click ▶ Start → Allow camera
````

> No other dependencies. Docker is all you need.

---

## 🏗️ Architecture

![Architecture Diagram](./architecture_diagram.png)

````
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  Browser ──► Nginx :80 ──► FastAPI Backend :8000        │
│     │           │               │         │             │
│     │      React SPA       WebSocket   REST API         │
│     │      (frontend)      /stream     /feed /roi       │
│     │                          │         │              │
│     └──── annotated JPEG ◄─────┘    PostgreSQL 16       │
│           (WebSocket)               sessions            │
│                                     frames              │
│                                     rois (AABB)         │
└─────────────────────────────────────────────────────────┘
````

| Service | Image | Purpose |
|---------|-------|---------|
| `nginx` | nginx:1.25-alpine | Reverse proxy, WS upgrade, single port |
| `backend` | python:3.12-slim | FastAPI, MediaPipe, Pillow annotation |
| `frontend` | node:20 → nginx | React SPA (multi-stage build) |
| `db` | postgres:16-alpine | Relational ROI storage |

---

## 🔌 API Design

### Endpoint 1 — Ingest Video Feed
````http
POST /api/v1/feed/start          # Create session → returns session_id
POST /api/v1/feed/{session_id}   # Push JPEG frame (multipart)
POST /api/v1/feed/{session_id}/stop
````

**Push frame response:**
````json
{
  "frame_index": 42,
  "face_detected": true,
  "roi": { "x": 249, "y": 125, "width": 184, "height": 184 }
}
````

### Endpoint 2 — Serve Annotated Stream
````
WS /api/v1/stream/{session_id}
````
Binary WebSocket — raw annotated JPEG bytes. Lime-green AABB drawn with **Pillow only, zero OpenCV**.

### Endpoint 3 — ROI Data
````http
GET /api/v1/roi/{session_id}?skip=0&limit=100   # Paginated
GET /api/v1/roi/{session_id}/latest             # Most recent
GET /health                                      # Liveness probe
````

---

## 🗄️ Database Schema

Designed for relational integrity — one ROI per frame, cascade deletes, indexed foreign keys.

````sql
sessions
  id          UUID PRIMARY KEY
  started_at  TIMESTAMPTZ
  ended_at    TIMESTAMPTZ
  client_ip   VARCHAR(45)
      │
      └── frames
            id            BIGINT PK
            session_id    UUID FK → sessions (CASCADE)
            frame_index   INT
            width/height  INT
            face_detected BOOLEAN
            captured_at   TIMESTAMPTZ
                │
                └── rois                    ← one-to-one with frame
                      id           BIGINT PK
                      frame_id     BIGINT FK → frames (CASCADE)
                      x, y         INT  ← top-left corner
                      width, height INT  ← axis-aligned bounding box
                      confidence   FLOAT
                      detected_at  TIMESTAMPTZ
````

Migrations managed by **Alembic** — run automatically on container start.

---

## 🧠 Face Detection Pipeline

````
JPEG bytes
    │
    ▼
Pillow decode → RGB array
    │
    ▼
MediaPipe FaceDetection (model_selection=0, CPU)
    │
    ▼
Relative bbox → absolute pixel coords
    │
    ▼
Pillow ImageDraw.rectangle (lime green, 3px)
    │
    ▼
JPEG encode → asyncio.Queue → WebSocket → Browser
    │
    ▼
PostgreSQL (frame + ROI row)
````

**No OpenCV used anywhere.** All image I/O and annotation is pure Pillow.

---

## 🛡️ Security

- CORS restricted via `CORS_ORIGINS` env var
- `client_max_body_size 5m` enforced at Nginx
- Frame content-type validated (JPEG only)
- PostgreSQL not exposed on host network
- Secrets externalised to `.env` (never committed)
- `X-Real-IP` / `X-Forwarded-For` forwarded correctly

---

## ⚙️ Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `facedetect` | DB user |
| `POSTGRES_PASSWORD` | `facedetect_secret` | **Change in production** |
| `POSTGRES_DB` | `facedetect` | Database name |
| `SECRET_KEY` | `supersecret...` | **Change in production** |
| `LOG_LEVEL` | `info` | debug / info / warning / error |
| `HOST_PORT` | `80` | Host port Nginx binds |

---

## 🧪 Testing

````bash
# Run all tests inside container
docker compose exec backend pytest -v

# Tests cover:
# ✓ Detection service — bbox math, clamping, invalid input
# ✓ BoundingBox — right/bottom properties
# ✓ Session store — create, get, close, sentinel
# ✓ API endpoints — 404, 415, health check
````

---

## 📁 Project Structure

````
facedetect/
├── backend/
│   ├── app/
│   │   ├── api/          # feed.py, stream.py, roi.py, health.py
│   │   ├── core/         # config.py, logging.py
│   │   ├── db/           # session.py, models.py
│   │   ├── models/       # schemas.py (Pydantic)
│   │   ├── services/     # detection.py, session_store.py
│   │   ├── tests/        # test_api.py
│   │   └── main.py
│   ├── alembic/          # migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # VideoPanel, StatsPanel, ROITable
│   │   ├── hooks/        # useCamera, useStreaming
│   │   ├── utils/        # api.js
│   │   └── App.jsx
│   └── Dockerfile
├── nginx/nginx.conf
├── scripts/init.sql
├── docker-compose.yml
└── .env.example
````

---

## 🤖 AI Collaboration Disclosure

This project was built with **Claude (Anthropic)** assistance. AI was used to generate:
- FastAPI router boilerplate and SQLAlchemy ORM models
- Alembic async migration setup
- MediaPipe detection wrapper and Pillow annotation logic
- React hooks (`useCamera`, `useStreaming`) and component structure

All generated code was reviewed, debugged, integrated, and tested by the developer. Architecture decisions, schema design, debugging, and deployment were directed by the developer.

---

## 📄 License

MIT © Aditya Kumar 2026
