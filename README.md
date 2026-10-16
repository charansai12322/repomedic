# 🩺 RepoMedic — AI-Assisted Static Security Auditing Product

RepoMedic is a modular, AI-assisted static code security auditing product designed to scan repositories for security vulnerabilities, exposed credentials, unsafe code patterns, and vulnerable dependencies.

Deterministic scanners discover the evidence; an LLM explains, prioritizes, and proposes concrete fixes under strict JSON schema constraints; and every AI claim is programmatically verified against scanner evidence before presentation.

---

## 🌟 What's New in Phase 2B

- 📁 **Modular Monorepo Structure**: Complete separation into `backend/` (FastAPI), `frontend/` (Next.js 16), and `docs/`, with preserved `RepoMedic.ipynb` at repository root.
- 📊 **OASIS SARIF 2.1.0 Exporter**: Full compliance with the SARIF 2.1.0 specification for seamless ingestion into CI/CD security pipelines, alongside interactive HTML and raw JSON exports.
- 📜 **Read-Only Git History Secret Scanner**: Inspects historical commits for credentials introduced and deleted in past revisions without modifying git refs or branches.
- 🎯 **Reproducible Security Benchmarking**: 16 offline synthetic fixtures with versioned ground truth, precision, recall, false positive rate, F1 score, and latency tracking.
- 🖥️ **Professional Security Dashboard**: Next.js App Router frontend with real-time polling, prominent **Partial Audit Warning** banner, severity breakdown, finding filters, and modal inspector.
- 🔐 **Secure BFF Architecture**: Backend credentials (`REPMEDIC_API_KEY`) are held strictly on the server; zero browser credential leakage.
- 🐳 **Containerization & Deployment Ready**: Multi-stage production Dockerfiles for backend and frontend orchestrated by root `docker-compose.yml`.

---

## 📁 Repository Structure

```text
RepoMedic/
├── backend/                  # FastAPI backend security engine
│   ├── repomedic/
│   │   ├── ai/               # Groq model discovery and triage prompts
│   │   ├── api/              # FastAPI application, auth middleware, and routes
│   │   ├── core/             # Orchestrator, rules, deduplication, scoring
│   │   ├── exports/          # Exporters: SARIF 2.1.0, HTML, JSON
│   │   ├── models/           # Domain models: findings, health, reports, jobs
│   │   ├── scanners/         # Custom AST, Semgrep, OSV, Git History scanners
│   │   ├── services/         # ScanService, JobService
│   │   ├── config.py         # Canonical configuration (pydantic-settings)
│   │   ├── exceptions.py     # Typed domain exception hierarchy
│   │   └── logging_config.py # Structured logging with secret sanitizer
│   ├── tests/                # Comprehensive test suite (unit, security, integration)
│   ├── benchmarks/           # 16 fixtures, ground truth, runner, and metrics
│   ├── main.py               # Local backend entrypoint
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Multi-stage production container
├── frontend/                 # Next.js App Router security dashboard
│   ├── src/
│   │   ├── app/              # Next.js pages (dashboard, new audit, results, benchmarks)
│   │   │   └── api/          # Server-side BFF proxy route handlers
│   │   ├── components/       # UI components (findings, health table, warning banner)
│   │   ├── lib/              # Formatters, client API, server proxy
│   │   └── types/            # TypeScript domain schemas
│   ├── tests/                # Frontend test suite (Node test runner)
│   ├── package.json          # Dependencies (React 19, Tailwind v4, Lucide)
│   └── Dockerfile            # Next.js production container
├── docs/                     # Architectural & operational documentation
│   ├── architecture.md       # Deep dive into system components and pipelines
│   ├── api.md                # Full REST API specification with request/response schemas
│   ├── security.md           # Threat model, SSRF defenses, redaction, subprocess rules
│   ├── benchmark-methodology.md # Benchmark corpus, ground truth, and metric math
│   └── deployment.md         # Docker Compose, manual setup, and environment config
├── docker-compose.yml        # Multi-container orchestration
├── RepoMedic.ipynb           # Interactive exploration notebook
├── pytest.ini                # Root pytest shim
├── main.py                   # Root backward-compatibility entrypoint
└── requirements.txt          # Root backward-compatibility dependencies
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)
```bash
# Build and run backend (:8000) and frontend (:3000)
docker compose up --build -d
```
- Open Dashboard: `http://localhost:3000`
- Open API Docs: `http://localhost:8000/docs`

### Option 2: Local Manual Startup

#### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
# Running on http://127.0.0.1:8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
# Running on http://localhost:3000
```

---

## 🧪 Quality Gates & Verification

### Run Backend Tests (118 tests)
```bash
# From repository root or backend/
python -m pytest -v
```

### Run Reproducible Benchmark Suite (16 fixtures)
```bash
# From repository root
python backend/benchmarks/runner.py

# Or from backend/
cd backend && python -m benchmarks.runner
```

### Run Frontend Tests & Build
```bash
cd frontend
# Run frontend unit tests
npm test

# Type checking
npx tsc --noEmit

# Production build
npm run build
```

---

## 📖 Detailed Documentation

- [System Architecture](docs/architecture.md)
- [REST API Reference](docs/api.md)
- [Security Model & Threat Defense](docs/security.md)
- [Benchmark Methodology & Metrics](docs/benchmark-methodology.md)
- [Deployment & Operations Guide](docs/deployment.md)

---

## ⚖️ License
Apache-2.0 or proprietary according to repository terms.