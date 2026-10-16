"""Finding normalization and cross-scanner deduplication."""

import hashlib
import re
from typing import Dict, List, Tuple
from repomedic.models.findings import Finding, Severity, Confidence


# Normalized category mapping for cross-scanner correlation
RULE_CATEGORY_MAP = [
    (re.compile(r"(?:eval|exec)", re.I), "code_injection:eval"),
    (re.compile(r"(?:pickle|marshal|deserializ)", re.I), "insecure_deserialization:pickle"),
    (re.compile(r"(?:yaml\.load|unsafe_yaml)", re.I), "insecure_deserialization:yaml"),
    (re.compile(r"(?:subprocess|os_system|shell_true)", re.I), "command_injection:shell"),
    (re.compile(r"(?:tls|verify_false|disabled-cert)", re.I), "tls:verification_off"),
    (re.compile(r"(?:sql|execute.*format)", re.I), "injection:sql"),
    (re.compile(r"(?:aws_access_key|aws-access-key)", re.I), "secret:aws_access_key"),
    (re.compile(r"(?:github_token|github-token)", re.I), "secret:github_token"),
    (re.compile(r"(?:private_key|private-key)", re.I), "secret:private_key"),
    (re.compile(r"(?:hardcoded_secret|secret-assignment)", re.I), "secret:hardcoded_credential"),
]

SEVERITY_ORDER = {
    Severity.CRITICAL: 5,
    Severity.HIGH: 4,
    Severity.MEDIUM: 3,
    Severity.LOW: 2,
    Severity.INFO: 1,
}

CONFIDENCE_ORDER = {
    Confidence.HIGH: 3,
    Confidence.MEDIUM: 2,
    Confidence.LOW: 1,
}


def normalize_rule_category(rule_id: str) -> str:
    """Normalizes scanner-specific rule IDs into generic flaw categories for correlation."""
    for pattern, category in RULE_CATEGORY_MAP:
        if pattern.search(rule_id):
            return category
    return rule_id.lower()


def compute_finding_fingerprint(finding: Finding) -> str:
    """
    Computes a deduplication fingerprint based on normalized file path, line number,
    and normalized rule category.
    """
    category = normalize_rule_category(finding.rule_id)
    # OSV dependencies are unique per package + vulnerability ID, not line number
    if finding.source == "osv":
        raw = f"{finding.file_path}|{finding.rule_id}"
    else:
        raw = f"{finding.file_path}|{finding.line_start}|{category}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def deduplicate_findings(findings: List[Finding]) -> List[Finding]:
    """
    Deduplicates findings across different scanners that report the same underlying
    vulnerability on the exact same line, merging corroborating evidence (Fixes AUDIT-003).
    """
    seen: Dict[str, Finding] = {}

    for finding in findings:
        fp = finding.fingerprint or compute_finding_fingerprint(finding)
        finding.fingerprint = fp

        if fp not in seen:
            seen[fp] = finding
        else:
            existing = seen[fp]
            # If the new finding has higher severity or higher confidence, promote it
            new_sev_rank = SEVERITY_ORDER.get(finding.severity, 0)
            cur_sev_rank = SEVERITY_ORDER.get(existing.severity, 0)

            # Record corroborating source
            if finding.source not in existing.corroborating_sources and finding.source != existing.source:
                existing.corroborating_sources.append(finding.source)

            # Preserve other rule ID in references
            ref_entry = f"corroborated_by:{finding.source}:{finding.rule_id}"
            if ref_entry not in existing.references:
                existing.references.append(ref_entry)

            if new_sev_rank > cur_sev_rank:
                # Promote severity
                existing.severity = finding.severity

            # If existing evidence was generic/withheld but new finding has concrete snippet, use it
            if "[Source excerpt withheld" in existing.evidence and finding.evidence and "[Source excerpt withheld" not in finding.evidence:
                existing.evidence = finding.evidence

    # Sort deterministically by severity rank (descending), file path, line number
    sorted_findings = sorted(
        seen.values(),
        key=lambda f: (-SEVERITY_ORDER.get(f.severity, 0), f.file_path, f.line_start, f.id)
    )
    return sorted_findings
