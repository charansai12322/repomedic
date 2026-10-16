"""Tests for AI triage schema validation, citation integrity, and deterministic fallback (Workstream 8)."""

import json
from unittest.mock import MagicMock, patch
from repomedic.ai.provider import groq_provider
from repomedic.ai.triage import AITriageEngine
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity
from repomedic.models.health import ScannerStatus


def make_dummy_finding(fid: str) -> Finding:
    return Finding(
        id=fid,
        title="Test Flaw",
        description="desc",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        source="custom_rules",
        rule_id="test_rule",
        file_path="app.py",
        line_start=10,
        line_end=10
    )


def test_ai_triage_deterministic_fallback_when_unconfigured():
    """When Groq key is not configured, engine returns deterministic-only summary without calling API."""
    engine = AITriageEngine(required=False)
    findings = [make_dummy_finding("F-real-1"), make_dummy_finding("F-real-2")]

    with patch.object(groq_provider, "client", None):
        result, health = engine.triage(findings, "https://github.com/test/repo")
        assert result.mode == "deterministic_only"
        assert len(result.diagnoses) == 0
        assert health.status == ScannerStatus.SKIPPED
        assert "deterministic findings" in result.executive_summary


def test_ai_citation_integrity_drops_hallucinated_ids():
    """Verifies that diagnoses referencing non-existent finding IDs are dropped, and citation validity is accurate."""
    engine = AITriageEngine(required=False)
    real_finding = make_dummy_finding("F-real-1234")

    # Mock LLM returning 1 real diagnosis and 1 hallucinated diagnosis
    llm_response_json = {
        "executive_summary": "Summary of critical vulnerabilities found.",
        "diagnoses": [
            {
                "finding_id": "F-real-1234",
                "title": "Real Vulnerability",
                "why_it_matters": "High risk",
                "fix": "Fix immediately",
                "priority": 1,
                "likely_false_positive": False
            },
            {
                "finding_id": "F-hallucinated-9999",
                "title": "Fabricated Finding",
                "why_it_matters": "Fake risk",
                "fix": "Do nothing",
                "priority": 2,
                "likely_false_positive": False
            }
        ],
        "limitations": ["Static analysis"]
    }

    mock_chat = MagicMock()
    mock_chat.choices = [MagicMock(message=MagicMock(content=json.dumps(llm_response_json)))]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_chat

    with patch.object(groq_provider, "client", mock_client):
        result, health = engine.triage([real_finding], "https://github.com/test/repo")

        assert health.status == ScannerStatus.COMPLETED
        # Verified that the hallucinated ID was dropped
        assert len(result.diagnoses) == 1
        assert result.diagnoses[0].finding_id == "F-real-1234"
        # 1 valid out of 2 proposed -> 50.0% validity
        assert result.citation_validity_percent == 50.0


def test_ai_triage_clean_repo_zero_findings():
    """When zero findings are detected, returns clean zero-finding result without LLM query."""
    engine = AITriageEngine(required=False)
    result, health = engine.triage([], "https://github.com/test/repo")
    assert health.status == ScannerStatus.COMPLETED
    assert len(result.diagnoses) == 0
    assert result.citation_validity_percent == 100.0
    assert "No security findings" in result.executive_summary
