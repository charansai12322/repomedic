# RepoMedic Security Benchmark Methodology

## 1. Corpus Design & Objectives

The RepoMedic benchmark suite provides an honest, repeatable, and offline evaluation framework for static analysis rules and vulnerability triage.

The evaluation corpus consists of **16 local, synthetic fixtures** under `backend/benchmarks/fixtures/`:

| Fixture ID | Category | Target Vulnerability Pattern | Negative Control? |
|---|---|---|---|
| `fix-01-hardcoded-secret` | Hardcoded Credentials | Hardcoded AWS secret key in Python code | No |
| `fix-02-subprocess-injection` | Subprocess Injection | Unsanitized user string in `subprocess.run(shell=True)` | No |
| `fix-03-sqli-string-concat` | SQL Injection | Direct string concatenation in DB query | No |
| `fix-04-path-traversal` | Path Traversal | Direct filename concatenation in file read | No |
| `fix-05-pickle-deserialization`| Deserialization | `pickle.loads` on untrusted input | No |
| `fix-06-flask-debug-true` | Insecure Config | Flask application running with `debug=True` | No |
| `fix-07-subprocess-alias` | Alias Evasion | `import subprocess as sp; sp.Popen(..., shell=True)` | No |
| `fix-08-os-system` | Command Execution | `os.system` with direct user input | No |
| `fix-09-vulnerable-dependency` | Dependency CVE | Manifest containing vulnerable package versions | No |
| `fix-10-clean-code` | Clean Baseline | Secure Python code with proper parameterization | **Yes** |
| `fix-11-eval-usage` | Code Execution | `eval(user_supplied_string)` | No |
| `fix-12-hardcoded-github-token`| Hardcoded Secret | Hardcoded `ghp_` GitHub personal access token | No |
| `fix-13-cors-wildcard` | Insecure Config | Permissive CORS `origins=["*"]` with credentials | No |
| `fix-14-yaml-unsafe-load` | Deserialization | `yaml.load(..., Loader=yaml.Loader)` | No |
| `fix-15-weak-hashing` | Cryptography | MD5 / SHA1 usage for password hashing | No |
| `fix-16-clean-deps` | Clean Dependencies | Secure, pinned package manifest with 0 CVEs | **Yes** |

---

## 2. Ground Truth & Matching Algorithm

Every fixture has a matching ground-truth specification in `backend/benchmarks/ground_truth/{fixture_id}.json`.

### Matching Algorithm
A scanner finding is matched to an expected ground-truth item if:
1. **File Path Match**: The finding's file path matches the expected file path (case-insensitive, normalized).
2. **Category / Rule Match**: The finding category matches or shares normalized vulnerability identifiers.
3. **Location Tolerance**: If expected line numbers are defined, the finding's line must fall within a ±5 line tolerance window.

If multiple scanner findings match the same ground-truth entry, only the first is counted as a **True Positive (TP)** to prevent double-counting; subsequent duplicates are treated as corroborating signals.

Findings on negative control fixtures (or unexpected findings on positive fixtures) are counted as **False Positives (FP)**.
Expected vulnerabilities that were not detected by any scanner are counted as **False Negatives (FN)**.
Clean fixtures that produced 0 findings are counted as **True Negatives (TN)**.

---

## 3. Mathematical Metrics Definitions

- **Precision**: $\frac{TP}{TP + FP}$ (Proportion of reported findings that were true vulnerabilities)
- **Recall**: $\frac{TP}{TP + FN}$ (Proportion of actual vulnerabilities detected)
- **False Positive Rate (FPR)**: $\frac{FP}{FP + TN}$
- **F1 Score**: $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$

*Note: When a denominator is zero, the system outputs `null` (not applicable) rather than inventing a percentage.*

---

## 4. Execution & Reproducibility

The benchmark runs completely offline without network dependencies or paid API keys:
```bash
# Run benchmark from backend/
python -m benchmarks.runner

# Or from repository root:
python backend/benchmarks/runner.py
```

Outputs are automatically generated to:
- `backend/benchmarks/results/benchmark_latest.json` (Machine-readable)
- `backend/benchmarks/results/benchmark_latest.md` (Human-readable Markdown)
