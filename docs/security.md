# RepoMedic Security Architecture & Threat Model

RepoMedic operates on untrusted code and repository URLs. Strict defense-in-depth security controls are enforced across all layers.

---

## 1. Threat Model & Boundaries

| Threat Vector | Mitigation Strategy | Enforcement Point |
|---|---|---|
| **Server-Side Request Forgery (SSRF)** | Strict URL scheme validation (`https://`, `ssh://`), blocking private CIDR blocks, link-local addresses, and AWS/GCP cloud metadata (`169.254.169.254`). | `core/cloner.py`, `frontend/src/lib/formatters.ts` |
| **Path Traversal & Symlink Escapes** | Path canonicalization (`resolve()`), verifying extracted/cloned paths stay strictly within isolated temporary sandbox directories. | `core/cloner.py`, `scanners/` |
| **Subprocess Command Injection** | Subprocesses invoked exclusively with list arguments (`shell=False`). Repository URLs and paths validated before invocation. | `scanners/semgrep.py`, `scanners/git_history.py` |
| **Resource Exhaustion (DoS)** | Timeouts per scan step (30s default), bounded concurrency (`MAX_CONCURRENT_SCANS`), bounded commit history depth, max file limits. | `config.py`, `services/job_service.py` |
| **Credential / Secret Leakage** | Automated token redaction on AST findings, Semgrep output, logs, SARIF exports, and AI prompt context. | `logging_config.py`, `core/sanitizer.py`, `exports/sarif_export.py` |
| **Prompt Injection via Source Code** | Model prompt fencing, findings treated as untrusted data, deterministic scanner evidence cannot be altered or overwritten by LLM triage. | `ai/triage.py` |
| **BFF Credential Leakage** | Server-side Next.js route handlers proxy requests with `REPMEDIC_API_KEY`. Browser JS never receives backend secrets. | `frontend/src/app/api/` |

---

## 2. In-Depth Security Mitigations

### 2.1 SSRF Defenses
RepoMedic verifies all remote repository URLs before executing `git clone` or network requests:
- Prohibited hostnames: `localhost`, `127.0.0.1`, `0.0.0.0`, `[::1]`, `169.254.169.254`.
- Prohibited IP spaces: RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), RFC 3927 link-local (`169.254.0.0/16`), loopback.
- Prohibited schemes: `file://`, `gopher://`, `ftp://`.

### 2.2 Read-Only Git History Scanning
The Git history scanner (`GitHistoryScanner`) inspects historical commits for accidentally committed secrets:
- Operates strictly in read-only mode via `git log -p -n {max_commits}`.
- Never performs `git checkout`, `git reset`, `git rebase`, or branch alterations.
- Bounded commit depth (default: 50 commits) prevents long-running traversal on large repositories.
- Temporary clone directories are deleted immediately following scan completion.

### 2.3 Secret Redaction & Sanitization
Before any finding is:
1. Written to logs,
2. Sent to the Groq AI API for triage,
3. Rendered in the HTML report,
4. Serialized in SARIF 2.1.0 output, or
5. Sent to the frontend dashboard,

RepoMedic replaces sensitive token patterns (OpenAI, Anthropic, AWS Access Keys, GitHub tokens, Slack Webhooks, RSA Private Keys) with sanitized asterisks (`AKIA****************`).

### 2.4 Evidence Integrity (Deterministic vs. AI)
- Deterministic findings (`custom_rules`, `semgrep`, `osv`) retain `evidence_quality: "deterministic"`.
- AI explanations, summaries, and triage categorizations are tagged `evidence_quality: "ai_interpretation"`.
- AI output can never suppress, delete, or alter the file path, line number, or rule ID of a deterministic scanner finding.
