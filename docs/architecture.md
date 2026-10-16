# RepoMedic Architecture

## 1. System Overview

RepoMedic is an AI-assisted static repository security auditing system designed for developer security analysis. It merges multi-engine deterministic vulnerability discovery (custom AST rules, Semgrep, OSV open-source vulnerability scanning, and read-only Git history scanning) with structured AI triage.

```
+-----------------------------------------------------------------------------------+
|                                Next.js Frontend                                   |
|  - Dashboard  - New Audit  - Live Polling  - Audit Results  - Benchmark Visuals   |
+-----------------------------------------------------------------------------------+
                                   | (Next.js Server Actions / BFF Route Handlers)
                                   v  [No API keys exposed to browser]
+-----------------------------------------------------------------------------------+
|                                RepoMedic Backend                                  |
|                                                                                   |
|  +--------------------+   +----------------------------------------------------+  |
|  | FastAPI Gateway    |-->| Job Service (Async threadpool queue / status state)|  |
|  | - Auth & SSRF Gate |   +----------------------------------------------------+  |
|  +--------------------+                              |                            |
|                                                      v                            |
|                               +-----------------------------------------------+   |
|                               | Scan Orchestrator                             |   |
|                               +-----------------------------------------------+   |
|                                 |          |              |             |         |
|                                 v          v              v             v         |
|                          +----------+ +---------+    +---------+   +------------+ |
|                          | Custom   | | Semgrep |    | OSV Dep |   | Git History| |
|                          | Rules    | | Scanner |    | Scanner |   | Scanner    | |
|                          +----------+ +---------+    +---------+   +------------+ |
|                                 \          |              |             /         |
|                                  \         |              |            /          |
|                               +-----------------------------------------------+   |
|                               | Finding Normalizer & Deduplicator             |   |
|                               +-----------------------------------------------+   |
|                                                      |                            |
|                                                      v                            |
|                               +-----------------------------------------------+   |
|                               | Groq AI Triage (Optional / Fallback Safe)     |   |
|                               +-----------------------------------------------+   |
|                                                      |                            |
|                                                      v                            |
|                               +-----------------------------------------------+   |
|                               | Export Engine (JSON / HTML / SARIF 2.1.0)     |   |
|                               +-----------------------------------------------+   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Monorepo Organization

```text
RepoMedic/
├── backend/
│   ├── repomedic/
│   │   ├── ai/            # Groq model discovery, triage prompt generation, client
│   │   ├── api/           # FastAPI application, auth middleware, route handlers
│   │   ├── core/          # Orchestrator, rule engine, deduplication, scoring
│   │   ├── exports/       # Exporters (SARIF 2.1.0 OASIS standard, HTML, JSON)
│   │   ├── models/        # Pydantic domain models (reports, findings, health, jobs)
│   │   ├── scanners/      # Custom AST, Semgrep, OSV, Git History scanners
│   │   ├── services/      # ScanService, JobService (lifecycle & queue)
│   │   ├── config.py      # Canonical settings (pydantic-settings)
│   │   ├── exceptions.py  # Domain hierarchy of typed exceptions
│   │   └── logging_config.py # Structured logging with secret sanitizer
│   ├── tests/             # Unit, security, and integration test suites
│   ├── benchmarks/        # Reproducible benchmark corpus, ground truth & runner
│   ├── main.py            # Local backend entrypoint
│   ├── Dockerfile         # Multi-stage production container
│   └── requirements.txt   # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js App Router (pages and BFF /api routes)
│   │   ├── components/    # Reusable UI components (findings, health, modal, badges)
│   │   ├── lib/           # Formatters, client API, server proxy
│   │   └── types/         # Strongly typed domain representations
│   ├── tests/             # Frontend unit test suite (Node test runner)
│   ├── package.json       # Dependencies (React 19, Next 16, Tailwind v4, Lucide)
│   └── Dockerfile         # Next.js production container
├── docs/                  # Architecture, API, Security, Benchmark & Deployment docs
├── docker-compose.yml     # Multi-container orchestration
└── RepoMedic.ipynb        # Preserved research and interactive exploration notebook
```

---

## 3. Core Subsystems

### 3.1 Scanner Subsystems
1. **Custom Rules Scanner (`CustomRulesScanner`)**:
   - Python AST visitor with alias resolution (e.g. `import subprocess as sp; sp.call(...)`).
   - Regex token inspection with redaction for credentials, AWS keys, GitHub tokens, and private keys.
   - Deterministic evidence quality (`deterministic`).
2. **Semgrep Integration (`SemgrepScanner`)**:
   - Bounded subprocess invocation executing targeted security rulesets.
   - Graceful fallback when Semgrep binary is absent; marks scanner as `unavailable`.
3. **OSV Dependency Scanner (`OSVScanner`)**:
   - Parses `requirements.txt`, `Pipfile.lock`, `package.json`, `package-lock.json`.
   - Queries OSV vulnerability databases with timeout safety and offline caching support.
4. **Git History Secret Scanner (`GitHistoryScanner`)**:
   - Read-only analysis via bounded `git log -p -n {max_commits}`.
   - Discovers credentials that were introduced in past commits and deleted from current tree.
   - Strictly read-only: no resets, checkouts, or ref modifications.

### 3.2 Evidence Quality and Confidence Model
Every finding strictly specifies:
- `evidence_quality`:
  - `"deterministic"`: Machine-verified by AST parser, Semgrep rule, or dependency database match.
  - `"ai_interpretation"`: Generated by LLM analysis; strictly annotated as unverified interpretation.
- `confidence`: Validated enumeration (`high`, `medium`, `low`). Model-generated confidence is never reported as calibrated probability.

### 3.3 Asynchronous Job Queue
- **Current Development Engine**: In-memory bounded queue utilizing Python's `concurrent.futures.ThreadPoolExecutor`.
- **State Transitions**: `queued` -> `running` -> `completed` / `partial` / `failed`.
- **Cancellation**: Explicit `POST /api/v1/jobs/{id}/cancel` updates state and terminates further processing safely.
- **Production Extension**: The architecture supports swapping the in-memory adapter for a Redis/Celery queue without modifying scanner or orchestration interfaces.

---

## 4. Frontend BFF Proxy Pattern

To ensure zero leakage of backend credentials:
- The frontend client communicates solely with Next.js Route Handlers (`/api/*`).
- Next.js server-side route handlers attach the `X-API-Key` (configured via server-only `REPMEDIC_API_KEY`) and proxy calls to the FastAPI backend.
- The browser never receives or possesses the `REPMEDIC_API_KEY` or `GROQ_API_KEY`.
