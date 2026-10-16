# RepoMedic REST API Specification

All endpoints are hosted under `/api/v1`. Protected endpoints require authentication when `REPMEDIC_API_KEY` is set in configuration.

## 1. Authentication
Include the API key in the request header:
```http
X-API-Key: your_repomedic_api_key_here
```
If an invalid or missing key is provided when authentication is enabled, the API returns:
```json
{
  "detail": "Invalid or missing API key."
}
```
HTTP Status: `401 Unauthorized`

---

## 2. Endpoints

### 2.1 Health & Readiness

#### `GET /api/v1/health`
Basic service liveness check. Does not require authentication.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "environment": "production"
}
```

#### `GET /api/v1/scanners/health`
Diagnostic inspection of all scanner subsystems and Groq AI availability.
- **Response `200 OK`**:
```json
{
  "scanners": {
    "custom_rules": {
      "status": "completed",
      "required": true,
      "duration_ms": 12.4,
      "finding_count": 0
    },
    "semgrep": {
      "status": "completed",
      "required": false,
      "duration_ms": 110.2,
      "finding_count": 0
    },
    "osv": {
      "status": "completed",
      "required": false,
      "duration_ms": 85.0,
      "finding_count": 0
    },
    "git_history": {
      "status": "skipped",
      "required": false,
      "duration_ms": 0.0,
      "finding_count": 0
    }
  },
  "audit_status": "complete",
  "partial_audit": false
}
```

---

### 2.2 Scans & Job Management

#### `POST /api/v1/scan`
Submit a new asynchronous repository audit.
- **Request Body**:
```json
{
  "repo_url": "https://github.com/example/sample-repo",
  "enable_ai": true,
  "enable_git_history": false,
  "max_history_commits": 50
}
```
- **Response `202 Accepted`**:
```json
{
  "job_id": "job_01j9x7k4e0z6w2m",
  "status": "queued",
  "created_at": "2026-10-14T17:30:00.000Z",
  "message": "Audit job queued successfully."
}
```

#### `GET /api/v1/jobs`
List recent scan jobs submitted to the system.
- **Query Parameters**:
  - `limit` (optional, integer, default: 20, max: 100)
- **Response `200 OK`**:
```json
[
  {
    "job_id": "job_01j9x7k4e0z6w2m",
    "status": "completed",
    "repo_url": "https://github.com/example/sample-repo",
    "created_at": "2026-10-14T17:30:00.000Z",
    "completed_at": "2026-10-14T17:30:15.000Z",
    "has_report": true
  }
]
```

#### `GET /api/v1/jobs/{job_id}`
Retrieve the execution status of a specific job.
- **Response `200 OK`**:
```json
{
  "job_id": "job_01j9x7k4e0z6w2m",
  "status": "completed",
  "repo_url": "https://github.com/example/sample-repo",
  "created_at": "2026-10-14T17:30:00.000Z",
  "completed_at": "2026-10-14T17:30:15.000Z",
  "has_report": true
}
```

#### `POST /api/v1/jobs/{job_id}/cancel`
Cancel an active or queued job.
- **Response `200 OK`**:
```json
{
  "job_id": "job_01j9x7k4e0z6w2m",
  "status": "failed",
  "error_message": "Job cancelled by user request."
}
```

---

### 2.3 Report Retrieval & Exports

#### `GET /api/v1/jobs/{job_id}/report`
Retrieve the scan audit report. Supports JSON, HTML, and SARIF 2.1.0.
- **Query Parameters**:
  - `format`: `json` (default) | `html` | `sarif`

##### JSON Response (`format=json`, Content-Type: `application/json`):
```json
{
  "id": "job_01j9x7k4e0z6w2m",
  "repository": "https://github.com/example/sample-repo",
  "timestamp": "2026-10-14T17:30:15.000Z",
  "scan_duration": 15.2,
  "audit_status": "complete",
  "partial_audit": false,
  "findings": [
    {
      "id": "find_01j9x7...",
      "title": "Hardcoded Credential in Source",
      "severity": "critical",
      "confidence": "high",
      "source": "custom_rules",
      "evidence_quality": "deterministic",
      "rule_id": "SEC001_HARDCODED_SECRET",
      "file_path": "config.py",
      "line_start": 14,
      "line_end": 14,
      "evidence": "AWS_SECRET = 'AKIA****************'",
      "remediation": "Move credential to environment variables.",
      "references": []
    }
  ],
  "scanner_health": { ... },
  "security_score": {
    "score": 75,
    "grade": "C",
    "penalty": 25,
    "severity_counts": { "critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0 }
  }
}
```

##### HTML Response (`format=html`, Content-Type: `text/html; charset=utf-8`):
Downloads or renders a standalone, self-contained HTML audit report with full CSS styling and table of findings.

##### SARIF Response (`format=sarif`, Content-Type: `application/sarif+json`):
Conforms to OASIS SARIF 2.1.0 standard schema:
```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "RepoMedic",
          "semanticVersion": "0.2.0",
          "rules": [ ... ]
        }
      },
      "results": [ ... ]
    }
  ]
}
```

---

### 2.4 Security Benchmarks

#### `GET /api/v1/benchmarks/summary`
Retrieve high-level summary metrics of the latest benchmark run.
- **Response `200 OK`**:
```json
{
  "available": true,
  "timestamp": "2026-10-14T17:05:00.000Z",
  "total_fixtures": 16,
  "precision": 0.7857,
  "recall": 0.7857,
  "f1_score": 0.7857,
  "false_positive_rate": 0.1429,
  "avg_scan_duration_sec": 0.05
}
```

#### `GET /api/v1/benchmarks/latest`
Retrieve full detailed benchmark results including per-fixture breakdown, categories, and scanner availability metrics.
