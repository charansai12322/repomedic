"""Tests for finding deduplication and cross-scanner merging (Fixes AUDIT-003)."""

from repomedic.core.deduplication import deduplicate_findings
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity


def test_cross_scanner_findings_merged_on_same_line():
    """
    Verifies that when custom AST scanner and Semgrep both flag the exact same line
    for an eval injection, they are merged into a single canonical finding with corroboration (Fixes AUDIT-003).
    """
    f1 = Finding(
        id="F-1111",
        title="Dynamic Code Execution (eval/exec)",
        description="eval() can execute attacker-controlled code dynamically.",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        source="python_ast",
        evidence_quality=EvidenceQuality.DETERMINISTIC,
        rule_id="py_eval_exec",
        file_path="app.py",
        line_start=9,
        line_end=9,
        evidence="eval(request.args['expr'])"
    )

    f2 = Finding(
        id="F-2222",
        title="Semgrep Rule Match: eval-injection",
        description="Detected user data flowing into eval.",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        source="semgrep",
        evidence_quality=EvidenceQuality.DETERMINISTIC,
        rule_id="semgrep:python.flask.security.injection.user-eval.eval-injection",
        file_path="app.py",
        line_start=9,
        line_end=9,
        evidence="[Source excerpt withheld; see file and line in repository.]"
    )

    deduped = deduplicate_findings([f1, f2])

    assert len(deduped) == 1, f"Expected 1 merged finding, got {len(deduped)}"
    merged = deduped[0]
    assert merged.file_path == "app.py"
    assert merged.line_start == 9
    assert "semgrep" in merged.corroborating_sources or "python_ast" in merged.corroborating_sources
    # Source excerpt should not be the withheld one if the AST snippet was available
    assert "[Source excerpt withheld" not in merged.evidence
    assert any("corroborated_by" in ref for ref in merged.references)


def test_different_lines_not_merged():
    """Findings on different lines must remain separate."""
    f1 = Finding(
        id="F-1111",
        title="eval line 9",
        description="eval",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        source="python_ast",
        rule_id="py_eval_exec",
        file_path="app.py",
        line_start=9,
        line_end=9
    )

    f2 = Finding(
        id="F-2222",
        title="eval line 15",
        description="eval",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        source="python_ast",
        rule_id="py_eval_exec",
        file_path="app.py",
        line_start=15,
        line_end=15
    )

    deduped = deduplicate_findings([f1, f2])
    assert len(deduped) == 2


def test_different_categories_on_same_line_not_merged():
    """Distinct flaws on the same line (e.g. hardcoded secret and debug flag) are not merged."""
    f1 = Finding(
        id="F-1111",
        title="Hardcoded Secret",
        description="secret",
        severity=Severity.CRITICAL,
        confidence=Confidence.HIGH,
        source="custom_rules",
        rule_id="secret:aws_access_key",
        file_path="app.py",
        line_start=20,
        line_end=20
    )

    f2 = Finding(
        id="F-2222",
        title="Debug Mode Enabled",
        description="debug",
        severity=Severity.MEDIUM,
        confidence=Confidence.HIGH,
        source="custom_rules",
        rule_id="debug_mode_enabled",
        file_path="app.py",
        line_start=20,
        line_end=20
    )

    deduped = deduplicate_findings([f1, f2])
    assert len(deduped) == 2
