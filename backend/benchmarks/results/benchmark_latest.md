# RepoMedic Security Benchmark Report

**Generated:** 2026-10-14 18:08:54 UTC  
**Evaluated Fixtures:** 16  

## Executive Summary

| Metric | Measured Value | Standard Formula |
| :--- | :--- | :--- |
| **Precision** | **78.6%** | `TP / (TP + FP)` |
| **Recall** | **78.6%** | `TP / (TP + FN)` |
| **F1 Score** | **78.6%** | `2 * (P * R) / (P + R)` |
| **False-Positive Rate (FPR)** | **60.0%** | `FP / (FP + TN)` |
| **AI Citation Validity** | **100.0%** | Programmatically verified against finding IDs |
| **Average Scan Time** | **6.19 ms** | Monotonic timer per fixture |
| **Median Scan Time** | **6.0 ms** | Monotonic timer per fixture |
| **Scanner Availability Rate** | **83.3%** | Non-failing scanner runs |
| **Partial Audit Rate** | **0.0%** | Fixtures with required scanner failure |

*Note: Synthetic benchmarks measure controlled regression performance across planted security patterns and negative controls; they do not represent universal coverage of real-world zero-day vulnerabilities.*

## Fixture Evaluation Breakdown

| Fixture ID | Fixture Name | Category | Result | Duration |
| :--- | :--- | :--- | :--- | :--- |
| `fix-01-aws-secret` | Hardcoded Synthetic AWS Key | Synthetic Issue | TP=1, FP=0, FN=0 | 8 ms |
| `fix-02-github-pat` | Hardcoded Synthetic GitHub PAT | Synthetic Issue | TP=1, FP=0, FN=0 | 5 ms |
| `fix-03-db-uri` | Database URI with Hardcoded Password | Synthetic Issue | TP=1, FP=0, FN=0 | 6 ms |
| `fix-04-private-key` | Private Key PEM Block | Synthetic Issue | TP=1, FP=0, FN=0 | 5 ms |
| `fix-05-subprocess-shell` | Subprocess Shell True | Synthetic Issue | TP=1, FP=0, FN=0 | 6 ms |
| `fix-06-sqli-fstring` | SQL Injection via String Formatting | Synthetic Issue | TP=0, FP=0, FN=1 | 6 ms |
| `fix-07-pickle-loads` | Insecure Deserialization via Pickle | Synthetic Issue | TP=0, FP=1, FN=1 | 6 ms |
| `fix-08-yaml-load` | Insecure YAML Load | Synthetic Issue | TP=0, FP=1, FN=1 | 7 ms |
| `fix-09-alias-os-system` | Aliased Import for os.system | Synthetic Issue | TP=1, FP=0, FN=0 | 7 ms |
| `fix-10-alias-subprocess` | Aliased Subprocess Module Call | Synthetic Issue | TP=1, FP=0, FN=0 | 6 ms |
| `fix-11-tls-disabled` | TLS Certificate Verification Disabled | Synthetic Issue | TP=1, FP=0, FN=0 | 6 ms |
| `fix-12-flask-debug` | Framework Debug Mode Enabled | Synthetic Issue | TP=1, FP=1, FN=0 | 7 ms |
| `fix-13-weak-hash` | Weak Hash Algorithm (MD5) | Synthetic Issue | TP=1, FP=0, FN=0 | 6 ms |
| `fix-14-eval-injection` | JavaScript Dynamic Eval Injection | Synthetic Issue | TP=1, FP=0, FN=0 | 6 ms |
| `fix-15-clean-python-app` | Clean Python Utility (Negative Control) | Negative Control | Passed (Clean) | 6 ms |
| `fix-16-clean-config-util` | Clean Configuration Utility (Negative Control) | Negative Control | Passed (Clean) | 6 ms |
