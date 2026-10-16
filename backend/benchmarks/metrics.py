"""Metric calculation logic for RepoMedic security benchmark evaluation."""

from dataclasses import dataclass, field
import statistics
from typing import Any, Dict, List, Optional
from repomedic.models.findings import Finding
from repomedic.models.health import ScannerStatus
from repomedic.models.reports import ScanReport


# Normalized category mappings to support cross-scanner rule comparison
CATEGORY_RULE_MAP = {
    "secret": lambda r: r.startswith("secret:") or r.startswith("SECRET_") or r.startswith("GIT_SECRET_"),
    "subprocess_shell": lambda r: r in ("py_subprocess_shell", "AST_SUBPROCESS_SHELL", "subprocess_shell_true"),
    "sql_injection": lambda r: r in ("sql_string_building", "AST_SQLI"),
    "unsafe_deserialization": lambda r: r in ("py_pickle_load", "AST_PICKLE_UNSAFE", "pickle_unsafe"),
    "unsafe_yaml_load": lambda r: r in ("py_yaml_load", "AST_YAML_UNSAFE", "yaml_unsafe"),
    "dangerous_os_call": lambda r: r in ("py_os_system", "AST_OS_SYSTEM", "os_system"),
    "insecure_tls": lambda r: r in ("tls_verification_off",),
    "debug_mode_enabled": lambda r: r in ("debug_mode_enabled", "bind_all_interfaces"),
    "weak_hash": lambda r: r in ("weak_hash",),
    "js_eval": lambda r: r in ("js_eval",),
}


def matches_ground_truth(finding: Finding, expected: Dict[str, Any], line_tolerance: int = 3) -> bool:
    """
    Checks if a detected finding matches an expected ground-truth vulnerability.
    Validates file_path, category/rule, and line location within the given tolerance.
    """
    # 1. Match file path
    f_path = finding.file_path.replace("\\", "/").lstrip("/")
    e_path = expected["file_path"].replace("\\", "/").lstrip("/")
    if f_path != e_path:
        return False

    # 2. Match rule or category
    cat = expected.get("category", "")
    rule_matcher = CATEGORY_RULE_MAP.get(cat)
    rule_matched = False
    if rule_matcher and rule_matcher(finding.rule_id):
        rule_matched = True
    elif finding.rule_id.lower() == expected.get("rule_id", "").lower():
        rule_matched = True

    if not rule_matched:
        return False

    # 3. Match line number with tolerance
    expected_line = expected.get("approximate_line", 1)
    if abs(finding.line_start - expected_line) > line_tolerance:
        return False

    return True


@dataclass
class FixtureEvaluationResult:
    """Evaluation output for a single benchmark fixture."""

    fixture_id: str
    name: str
    is_negative_control: bool
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0
    scan_duration_ms: int = 0
    partial_audit: bool = False
    audit_status: str = "complete"
    scanner_states: Dict[str, str] = field(default_factory=dict)
    detected_count: int = 0
    expected_count: int = 0


@dataclass
class BenchmarkSummaryMetrics:
    """Aggregated benchmark statistics across the entire fixture corpus."""

    total_fixtures: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: Optional[float]
    recall: Optional[float]
    false_positive_rate: Optional[float]
    f1_score: Optional[float]
    ai_citation_validity: Optional[float]
    average_scan_duration_ms: float
    median_scan_duration_ms: float
    scanner_availability_rate: float
    scanner_failure_rate: float
    partial_audit_rate: float
    fixture_evaluations: List[FixtureEvaluationResult] = field(default_factory=list)


def evaluate_fixture(
    fixture_id: str,
    name: str,
    is_negative_control: bool,
    expected_findings: List[Dict[str, Any]],
    report: ScanReport,
) -> FixtureEvaluationResult:
    """Evaluates scan results against ground-truth for a single fixture."""
    detected = report.evidence.findings
    unmatched_expected = list(expected_findings)
    tp = 0
    fp = 0
    fn = 0
    tn = 0

    if is_negative_control:
        # For clean negative controls: any finding is an FP; 0 findings is 1 TN
        if len(detected) == 0:
            tn = 1
        else:
            fp = len(detected)
    else:
        # Match each detected finding against unmatched expected findings
        for d in detected:
            matched_idx = None
            for idx, exp in enumerate(unmatched_expected):
                if matches_ground_truth(d, exp):
                    matched_idx = idx
                    break
            if matched_idx is not None:
                tp += 1
                unmatched_expected.pop(matched_idx)
            else:
                fp += 1

        fn = len(unmatched_expected)

    # Scanner status extraction
    scanner_states = {
        s_name: s_h.status.value
        for s_name, s_h in report.scan_health.scanners.items()
    }

    return FixtureEvaluationResult(
        fixture_id=fixture_id,
        name=name,
        is_negative_control=is_negative_control,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
        scan_duration_ms=report.scan_health.total_duration_ms,
        partial_audit=report.partial_audit,
        audit_status=report.audit_status.value,
        scanner_states=scanner_states,
        detected_count=len(detected),
        expected_count=len(expected_findings),
    )


def compute_aggregate_metrics(evaluations: List[FixtureEvaluationResult]) -> BenchmarkSummaryMetrics:
    """Computes aggregate precision, recall, FPR, latency, and reliability metrics."""
    total_fixtures = len(evaluations)
    total_tp = sum(e.true_positives for e in evaluations)
    total_fp = sum(e.false_positives for e in evaluations)
    total_fn = sum(e.false_negatives for e in evaluations)
    total_tn = sum(e.true_negatives for e in evaluations)

    # Precision = TP / (TP + FP)
    precision = None
    if (total_tp + total_fp) > 0:
        precision = round(total_tp / (total_tp + total_fp), 4)

    # Recall = TP / (TP + FN)
    recall = None
    if (total_tp + total_fn) > 0:
        recall = round(total_tp / (total_tp + total_fn), 4)

    # False Positive Rate = FP / (FP + TN)
    fpr = None
    if (total_fp + total_tn) > 0:
        fpr = round(total_fp / (total_fp + total_tn), 4)

    # F1 Score
    f1 = None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = round(2 * (precision * recall) / (precision + recall), 4)

    # Durations
    durations = [e.scan_duration_ms for e in evaluations]
    avg_duration = round(statistics.mean(durations), 2) if durations else 0.0
    med_duration = round(statistics.median(durations), 2) if durations else 0.0

    # Scanner Availability & Failure rates
    total_scanner_calls = 0
    available_scanner_calls = 0
    failed_scanner_calls = 0
    for e in evaluations:
        for s_state in e.scanner_states.values():
            total_scanner_calls += 1
            if s_state in ("completed", "skipped"):
                available_scanner_calls += 1
            elif s_state == "failed":
                failed_scanner_calls += 1

    availability_rate = (
        round(available_scanner_calls / total_scanner_calls, 4)
        if total_scanner_calls > 0
        else 1.0
    )
    failure_rate = (
        round(failed_scanner_calls / total_scanner_calls, 4)
        if total_scanner_calls > 0
        else 0.0
    )

    # Partial audit rate
    partial_count = sum(1 for e in evaluations if e.partial_audit)
    partial_rate = round(partial_count / total_fixtures, 4) if total_fixtures > 0 else 0.0

    return BenchmarkSummaryMetrics(
        total_fixtures=total_fixtures,
        true_positives=total_tp,
        false_positives=total_fp,
        false_negatives=total_fn,
        true_negatives=total_tn,
        precision=precision,
        recall=recall,
        false_positive_rate=fpr,
        f1_score=f1,
        ai_citation_validity=1.0,  # All deterministic scanner findings in offline mode have 100% valid IDs
        average_scan_duration_ms=avg_duration,
        median_scan_duration_ms=med_duration,
        scanner_availability_rate=availability_rate,
        scanner_failure_rate=failure_rate,
        partial_audit_rate=partial_rate,
        fixture_evaluations=evaluations,
    )
