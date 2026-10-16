# RepoMedic Backend

The modular FastAPI-powered security auditing engine for RepoMedic.

## Features
- **Deterministic Static Scanners**: Custom AST rules with import-alias resolution, Semgrep integration, and OSV dependency scanning.
- **Git History Secret Scanner**: Optional, read-only historical commit inspection for deleted/stale credentials.
- **SARIF 2.1.0 Exporter**: OASIS standard SARIF report generation alongside JSON and interactive HTML reports.
- **Reproducible Security Benchmarks**: 16 offline synthetic test fixtures with precision, recall, and false positive metrics.
- **Asynchronous Job Engine**: Background queue with explicit states, timeouts, and cancellation controls.
- **Groq AI Triage**: Optional LLM summarization and remediation advice with strict separation between deterministic evidence and AI interpretations.

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start backend server
python main.py
# Server runs on http://127.0.0.1:8000
# OpenAPI Docs: http://127.0.0.1:8000/docs
```

## Running Tests
```bash
# Run complete test suite (unit, security, integration)
pytest tests -v

# Run with test coverage
pytest --cov=repomedic --cov-report=term-missing
```

## Running Security Benchmarks
```bash
# Execute offline benchmark evaluation
python -m benchmarks.runner
```
Results will be output to `benchmarks/results/benchmark_latest.json` and `benchmarks/results/benchmark_latest.md`.
