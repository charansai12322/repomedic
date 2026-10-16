"""Unit tests for security benchmark metric computations."""

from benchmarks.metrics import (
    FixtureEvaluationResult,
    compute_aggregate_metrics,
    matches_ground_truth,
)
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity


def test_matches_ground_truth_tolerance():
    finding = Finding(
        id="F-1",
        title="Subprocess Injection",
        description="shell=True",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        source="python_ast",
        evidence_quality=EvidenceQuality.DETERMINISTIC,
        rule_id="py_subprocess_shell",
        file_path="src/worker.py",
        line_start=10,
        line_end=10,
    )
    expected = {
        "category": "subprocess_shell",
        "file_path": "src/worker.py",
        "approximate_line": 12,  # Within tolerance of 3
    }
    assert matches_ground_truth(finding, expected, line_tolerance=3) is True

    # Beyond tolerance
    expected_far = {
        "category": "subprocess_shell",
        "file_path": "src/worker.py",
        "approximate_line": 20,
    }
    assert matches_ground_truth(finding, expected_far, line_tolerance=3) is False


def test_compute_aggregate_metrics_calculations():
    evals = [
        FixtureEvaluationResult(
            fixture_id="f1",
            name="Issue 1",
            is_negative_control=False,
            true_positives=1,
            false_positives=0,
            false_negatives=0,
            true_negatives=0,
            scan_duration_ms=10,
            scanner_states={"ast": "completed"},
        ),
        FixtureEvaluationResult(
            fixture_id="f2",
            name="Issue 2",
            is_negative_control=False,
            true_positives=1,
            false_positives=1,
            false_negatives=1,
            true_negatives=0,
            scan_duration_ms=20,
            scanner_states={"ast": "completed"},
        ),
        FixtureEvaluationResult(
            fixture_id="f3",
            name="Clean Control",
            is_negative_control=True,
            true_positives=0,
            false_positives=0,
            false_negatives=0,
            true_negatives=1,
            scan_duration_ms=30,
            scanner_states={"ast": "completed"},
        ),
    ]

    metrics = compute_aggregate_metrics(evals)

    assert metrics.total_fixtures == 3
    assert metrics.true_positives == 2
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.true_negatives == 1

    # Precision = 2 / (2 + 1) = 0.6667
    assert metrics.precision == 0.6667
    # Recall = 2 / (2 + 1) = 0.6667
    assert metrics.recall == 0.6667
    # FPR = 1 / (1 + 1) = 0.5
    assert metrics.false_positive_rate == 0.5
    assert metrics.average_scan_duration_ms == 20.0
    assert metrics.median_scan_duration_ms == 20.0
