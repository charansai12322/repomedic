"""Integration tests for orchestrator and local scan execution."""

from pathlib import Path
from repomedic.core.orchestrator import ScannerOrchestrator
from repomedic.models.health import AuditStatus
from repomedic.services.scan_service import ScanService


def test_orchestrator_scans_synthetic_vulnerable_repository(temp_repo_dir: Path):
    """Verifies end-to-end scanner orchestration against a local synthetic repository."""
    # 1. Create vulnerable files
    (temp_repo_dir / "app.py").write_text(
        """import os, pickle, subprocess, yaml
from flask import Flask, request
app = Flask(__name__)

@app.route('/run')
def run():
    subprocess.run(request.args['cmd'], shell=True)
    return str(eval(request.args['expr']))

@app.route('/load', methods=['POST'])
def load():
    obj = pickle.loads(request.data)
    cfg = yaml.load(request.data)
    return 'ok'
""",
        encoding="utf-8"
    )

    (temp_repo_dir / "config.py").write_text(
        'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7REALKEY"\n',
        encoding="utf-8"
    )

    (temp_repo_dir / "requirements.txt").write_text(
        "flask==0.12.2\nrequests==2.19.0\n",
        encoding="utf-8"
    )

    # 2. Run orchestrator
    orchestrator = ScannerOrchestrator()
    findings, health, score, evidence = orchestrator.run_all_scanners(temp_repo_dir)

    # Health checks
    assert "custom_rules" in health.scanners
    assert "python_ast" in health.scanners
    assert health.audit_status in (AuditStatus.COMPLETE, AuditStatus.PARTIAL)

    # Findings checks
    rule_ids = {f.rule_id for f in findings}
    assert "secret:aws_access_key" in rule_ids
    assert "py_subprocess_shell" in rule_ids
    assert "py_eval_exec" in rule_ids
    assert "py_unsafe_deserialization" in rule_ids
    assert "py_yaml_unsafe_load" in rule_ids

    # Critical finding clamps score to <= 69 and grade C or lower
    assert score.score <= 69
    assert score.grade in ("C", "D", "F")
    assert evidence.files_scanned >= 3


def test_scan_service_local_dir_execution(temp_repo_dir: Path):
    """Verifies ScanService running on a local directory produces a complete ScanReport."""
    (temp_repo_dir / "app.py").write_text("print('clean')", encoding="utf-8")

    service = ScanService()
    report = service.execute_scan("local://test-repo", local_dir=temp_repo_dir)

    assert report.target == "local://test-repo"
    assert report.score.score == 100
    assert report.score.grade == "A"
    assert report.ai_triage.mode in ("deterministic_only", "groq")
    assert report.scan_health.audit_status == AuditStatus.COMPLETE
