# FaceDetect · Real-Time Face Detection System

> Containerised full-stack system: WebSocket video streaming, dlib-based face detection (no OpenCV), PostgreSQL ROI persistence, React frontend.

---

## Quick start (< 5 minutes)

```bash
git clone <repo-url> facedetect && cd facedetect

cp .env.example .env          # edit secrets if desired

docker compose up --build     # first build takes ~5 min (dlib compiles from source)
```

Open **http://localhost** → click **▶ Start** → allow camera → watch faces get boxed in real-time.

---

## Architecture

```
Browser
  ├── POST /api/v1/feed/{id}      →  Backend (ingest JPEG frames)
  ├── WS   /api/v1/stream/{id}    →  Backend (receive annotated JPEG stream)
  └── GET  /api/v1/roi/{id}       →  Backend (fetch ROI data)

                        ↕ asyncpg
                    PostgreSQL 16
                  sessions / frames / rois

All traffic routes through Nginx (port 80) as a reverse proxy.
```

See `architecture_diagram.png` for the full visual.

### Services

| Container | Image | Purpose |
|-----------|-------|---------|
| `nginx`   | nginx:1.25-alpine | Reverse proxy, WS upgrade, single ingress |
| `backend` | python:3.12-slim (custom) | FastAPI app + face detection |
| `frontend`| node:20-alpine → nginx:1.25-alpine | React SPA (multi-stage build) |
| `db`      | postgres:16-alpine | ROI persistence |

---

## API Reference

### Endpoint 1 – Receive video feed

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/feed/start` | Create session → returns `session_id` |
| `POST` | `/api/v1/feed/{session_id}` | Push JPEG frame (multipart `frame_file`) |
| `POST` | `/api/v1/feed/{session_id}/stop` | End session |

**Push frame response**
```json
{
  "frame_index": 42,
  "face_detected": true,
  "roi": { "x": 120, "y": 80, "width": 150, "height": 180 }
}
```

### Endpoint 2 – Serve video feed (WebSocket)

```
WS /api/v1/stream/{session_id}
```

Binary messages: raw annotated JPEG bytes. Text `"ping"` messages keep-alive.
The annotated frame has a lime-green bounding box drawn **with Pillow only** — no OpenCV.

### Endpoint 3 – ROI data

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/roi/{session_id}?skip=0&limit=100` | Paginated frame+ROI records |
| `GET` | `/api/v1/roi/{session_id}/latest` | Most recent ROI |
| `GET` | `/health` | Liveness probe |

---

## Database schema

```sql
sessions (id UUID PK, started_at, ended_at, client_ip)
    │
    └── frames (id bigint PK, session_id FK, frame_index, width, height,
                face_detected, captured_at)
                    │
                    └── rois (id bigint PK, frame_id FK unique,
                               x, y, width, height,   ← axis-aligned bounding box
                               confidence, detected_at)
```

Managed by **Alembic** (async migrations run on container start).

---

## Face detection

- Library: [`face_recognition`](https://github.com/ageitgey/face_recognition) (wraps **dlib** HOG detector)
- **No OpenCV** used anywhere — all image I/O and annotation uses **Pillow**
- Frames are downscaled to ≤ 640px before detection (configurable `DETECTION_MAX_DIM`)
- Bounding box coordinates are scaled back to original resolution before annotation and storage

---

## Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `facedetect` | DB user |
| `POSTGRES_PASSWORD` | `facedetect_secret` | DB password (**change in prod**) |
| `POSTGRES_DB` | `facedetect_db` | Database name |
| `SECRET_KEY` | `...` | App secret (**change in prod**) |
| `LOG_LEVEL` | `info` | `debug \| info \| warning \| error` |
| `CORS_ORIGINS` | `http://localhost` | Comma-separated allowed origins |
| `HOST_PORT` | `80` | Host port nginx binds |

---

## Running tests

```bash
# Inside the backend container
docker compose exec backend pytest -v

# Or locally (requires Python 3.12 + pip install -r requirements.txt)
cd backend && pytest -v
```

---

## Development workflow

```bash
# Live-reload backend
docker compose exec backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Live-reload frontend (Vite HMR)
cd frontend && npm run dev   # proxies /api and /ws to localhost:8000
```

---

## Security notes

- CORS restricted to `CORS_ORIGINS` env var
- `X-Forwarded-For` / `X-Real-IP` forwarded by nginx
- Frame content-type validated (only `image/jpeg` accepted)
- `client_max_body_size 5m` enforced at nginx
- PostgreSQL not exposed on host network (internal Docker network only)
- Secret key / DB password externalised to `.env` (never committed)

---

## AI collaboration disclosure

This project was built with AI assistance (Claude Sonnet). The AI generated:
- Initial boilerplate for FastAPI routers, SQLAlchemy models, Alembic migrations
- The face detection service wrapper and Pillow annotation logic
- React component structure and WebSocket hook

All generated code was reviewed, tested, and adapted. Architecture decisions, schema design, and integration were directed by the developer. Test cases were written to verify correctness of core logic independently of the AI-generated code.

---

## License

MIT
