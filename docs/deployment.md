# RepoMedic Deployment & Operational Guide

## 1. Quick Start via Docker Compose

The quickest method to spin up both the FastAPI backend and the Next.js frontend is using Docker Compose:

```bash
# 1. Clone repository
git clone https://github.com/charansai12322/repomedic.git
cd repomedic

# 2. Configure environment (copy example)
cp backend/.env.example backend/.env

# 3. Build and launch services
docker compose up --build -d
```

- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`

---

## 2. Local Development Setup (Without Docker)

### 2.1 Backend Setup
```bash
cd backend
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

pip install -r requirements.txt
# Optional: install Semgrep for AST rules
pip install semgrep

# Start development server
python main.py
# Server listens at http://127.0.0.1:8000
```

### 2.2 Frontend Setup
```bash
cd frontend
npm install

# Start development server
npm run dev
# Dashboard listens at http://localhost:3000
```

---

## 3. Environment Variables Reference

### Backend Configuration (`backend/.env`)

| Variable | Description | Default | Production Note |
|---|---|---|---|
| `REPMEDIC_ENV` | Operating environment (`development`, `production`, `test`) | `development` | Set to `production` in production. |
| `REPMEDIC_API_KEY` | Shared secret token for API authentication | `None` (open dev mode) | **Mandatory** in production. Must be a cryptographically random secret. |
| `GROQ_API_KEY` | API key for Groq LLM inference service | `None` (deterministic only) | Optional in offline dev; required for Phase 3 AI triage. |
| `GROQ_MODEL` | Default model identifier for Groq AI | `llama-3.3-70b-versatile` | Configurable based on available Groq models. |
| `REPMEDIC_ENABLE_GIT_HISTORY` | Enables read-only historical git commit secret scanning | `false` | Disabled by default. |
| `REPMEDIC_MAX_CONCURRENT_SCANS` | Maximum parallel scans processed by threadpool | `2` | Bound according to available server CPU/RAM. |
| `REPMEDIC_MAX_HISTORY_COMMITS` | Maximum commit depth for git history scanning | `50` | Prevents long-running traversals on huge repos. |

### Frontend Configuration (`frontend/.env.local`)

| Variable | Description | Default | Security Notice |
|---|---|---|---|
| `REPMEDIC_BACKEND_URL` | Upstream FastAPI backend base URL | `http://127.0.0.1:8000` | Server-side only; never prefix with `NEXT_PUBLIC_`. |
| `REPMEDIC_API_KEY` | API key forwarded by BFF route handlers to backend | `None` | Kept strictly on Next.js server; never sent to browser client. |

---

## 4. Asynchronous Queue Architecture & Durability

### Current Implementation: In-Memory Adapter
- **Mechanics**: Implemented using Python's `concurrent.futures.ThreadPoolExecutor` and in-memory thread-safe dictionaries.
- **Suitability**: Excellent for single-instance deployments, local evaluation, CI/CD pipelines, and development.
- **Limitations**: Job statuses and reports are volatile; restarting the server process will clear queued and historical jobs.

### Durable Production Architecture
For multi-instance horizontal scaling, the backend is architected to support a Redis-backed queue (Celery or RQ):
- **Queue**: Redis instance storing job tasks and message channels.
- **Workers**: Dedicated worker containers executing `repomedic.core.orchestrator.ScanOrchestrator`.
- **Report Store**: Shared S3/GCS bucket or persistent PostgreSQL database holding serialized JSON/SARIF audit records.
