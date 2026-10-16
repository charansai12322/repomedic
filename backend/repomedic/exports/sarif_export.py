"""SARIF 2.1.0 exporter for RepoMedic scan reports."""

import json
from typing import Any, Dict, List
from repomedic.core.sanitization import sanitize
from repomedic.models.findings import EvidenceQuality, Finding, Severity
from repomedic.models.health import AuditStatus
from repomedic.models.reports import ScanReport


SEVERITY_TO_SARIF_LEVEL = {
    Severity.CRITICAL: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
    Severity.INFO: "none",
}


def finding_to_sarif_result(finding: Finding) -> Dict[str, Any]:
    """Converts a canonical RepoMedic Finding into a standard SARIF 2.1.0 Result object with sanitized evidence."""
    level = SEVERITY_TO_SARIF_LEVEL.get(finding.severity, "warning")

    # Ensure valid line bounds
    start_line = max(1, finding.line_start)
    end_line = max(start_line, finding.line_end)

    safe_title = sanitize(finding.title, limit=300)
    safe_desc = sanitize(finding.description, limit=1000)
    safe_evidence = sanitize(finding.evidence, limit=2000) if finding.evidence else ""

    result: Dict[str, Any] = {
        "ruleId": finding.rule_id,
        "level": level,
        "message": {
            "text": f"{safe_title}: {safe_desc}"
        },
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": finding.file_path,
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": start_line,
                        "endLine": end_line,
                    },
                }
            }
        ],
        "properties": {
            "finding_id": finding.id,
            "source": finding.source,
            "confidence": finding.confidence.value,
            "evidence_quality": finding.evidence_quality.value,
            "sanitized_evidence": safe_evidence,
            "remediation": finding.remediation,
            "references": finding.references,
            "corroborating_sources": finding.corroborating_sources,
        },
    }
    return result


def export_report_to_sarif_dict(report: ScanReport) -> Dict[str, Any]:
    """
    Serializes a ScanReport into a complete, valid SARIF 2.1.0 dictionary.
    Handles empty findings, partial audits, and missing external scanners cleanly.
    """
    rules_map: Dict[str, Dict[str, Any]] = {}
    sarif_results: List[Dict[str, Any]] = []

    for finding in report.evidence.findings:
        # Build driver rule descriptor if not already recorded
        if finding.rule_id not in rules_map:
            rules_map[finding.rule_id] = {
                "id": finding.rule_id,
                "name": finding.title.replace(" ", "_"),
                "shortDescription": {
                    "text": finding.title
                },
                "fullDescription": {
                    "text": finding.description
                },
                "defaultConfiguration": {
                    "level": SEVERITY_TO_SARIF_LEVEL.get(finding.severity, "warning")
                },
                "help": {
                    "text": finding.remediation or "Refer to project security guidelines."
                },
                "properties": {
                    "tags": ["security", "static-analysis", finding.source],
                    "precision": "high" if finding.evidence_quality == EvidenceQuality.DETERMINISTIC else "medium",
                },
            }

        sarif_results.append(finding_to_sarif_result(finding))

    # Evaluate invocation health
    execution_successful = (
        not report.partial_audit
        and report.audit_status == AuditStatus.COMPLETE
    )

    invocations = [
        {
            "executionSuccessful": execution_successful,
            "endTimeUtc": report.scan_health.finish_time,
            "startTimeUtc": report.scan_health.start_time,
            "properties": {
                "audit_status": report.audit_status.value,
                "partial_audit": report.partial_audit,
                "total_duration_ms": report.scan_health.total_duration_ms,
                "scanners": {
                    name: {
                        "status": h.status.value,
                        "required": h.required,
                        "duration_ms": h.duration_ms,
                        "finding_count": h.finding_count,
                        "error_code": h.error_code,
                    }
                    for name, h in report.scan_health.scanners.items()
                },
            },
        }
    ]

    sarif_doc: Dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "RepoMedic",
                        "version": "2.0.0",
                        "informationUri": "https://github.com/charansai12322/repomedic",
                        "rules": list(rules_map.values()),
                    }
                },
                "invocations": invocations,
                "results": sarif_results,
                "properties": {
                    "target": report.target,
                    "security_score": report.score.score,
                    "grade": report.score.grade,
                    "files_scanned": report.evidence.files_scanned,
                },
            }
        ],
    }

    return sarif_doc


def export_report_to_sarif_json(report: ScanReport, indent: int = 2) -> str:
    """Serializes a ScanReport to formatted SARIF 2.1.0 JSON text."""
    doc = export_report_to_sarif_dict(report)
    return json.dumps(doc, indent=indent)
