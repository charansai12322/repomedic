"""Deterministic security scoring and letter-grade calculation."""

from collections import Counter
import math
from typing import List
from repomedic.models.findings import Finding, Severity
from repomedic.models.reports import SecurityScore


WEIGHTS = {
    Severity.CRITICAL: 20,
    Severity.HIGH: 8,
    Severity.MEDIUM: 3,
    Severity.LOW: 1,
    Severity.INFO: 0,
}

PER_RULE_CAP = 5


def compute_rule_grouping_key(finding: Finding) -> str:
    """
    Computes a grouping key for per-rule penalty capping.
    For OSV dependency CVEs ('osv:<VULN_ID>:<PACKAGE_NAME>'), group by package ('osv:<PACKAGE_NAME>')
    so that one vulnerable package with 20 CVEs is capped, but vulnerabilities in different
    packages are fairly penalized (Fixes AUDIT-004).
    """
    rule_id = finding.rule_id
    if rule_id.startswith("osv:"):
        parts = rule_id.split(":")
        if len(parts) >= 3:
            return f"osv:{parts[2].lower()}"
    return rule_id


def compute_security_score(findings: List[Finding]) -> SecurityScore:
    """
    Computes an explainable, deterministic security score (0-100) and letter grade (A-F)
    using an exponential penalty curve with per-rule capping and critical finding clamping.
    """
    if not findings:
        return SecurityScore(
            score=100,
            grade="A",
            penalty=0,
            severity_counts={s.value: 0 for s in Severity}
        )

    counts = Counter(f.severity for f in findings)
    per_rule_count = Counter()
    total_penalty = 0

    for finding in findings:
        group_key = compute_rule_grouping_key(finding)
        per_rule_count[group_key] += 1
        if per_rule_count[group_key] <= PER_RULE_CAP:
            weight = WEIGHTS.get(finding.severity, 0)
            total_penalty += weight

    # Exponential decay: 60 points of penalty halves the score from ~100 to ~37
    raw_score = round(100 * math.exp(-total_penalty / 60.0))
    raw_score = max(0, min(100, raw_score))

    # Grade and critical clamping policy: Any critical finding caps the score at 69 (Grade C max)
    if counts[Severity.CRITICAL] > 0:
        raw_score = min(raw_score, 69)

    if raw_score >= 90:
        grade = "A"
    elif raw_score >= 80:
        grade = "B"
    elif raw_score >= 65:
        grade = "C"
    elif raw_score >= 50:
        grade = "D"
    else:
        grade = "F"

    severity_counts = {s.value: counts.get(s, 0) for s in Severity}

    return SecurityScore(
        score=raw_score,
        grade=grade,
        penalty=total_penalty,
        severity_counts=severity_counts
    )
