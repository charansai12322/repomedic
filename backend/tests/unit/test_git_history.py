"""Unit tests for read-only Git history scanner."""

import os
from pathlib import Path
import subprocess
import pytest
from repomedic.models.health import ScannerStatus
from repomedic.scanners.git_history import GitHistoryScanner


def test_git_history_disabled_by_default(temp_repo_dir: Path):
    scanner = GitHistoryScanner(enabled=False)
    findings, health = scanner.scan(temp_repo_dir)

    assert findings == []
    assert health.status == ScannerStatus.SKIPPED
    assert "disabled" in health.diagnostic_message.lower()


def test_git_history_non_git_repo_skipped(temp_repo_dir: Path):
    scanner = GitHistoryScanner(enabled=True)
    findings, health = scanner.scan(temp_repo_dir)

    assert findings == []
    assert health.status == ScannerStatus.SKIPPED
    assert "not a git repository" in health.diagnostic_message.lower()


def test_git_history_detects_removed_secret(tmp_path: Path):
    repo_dir = tmp_path / "synthetic_git_repo"
    repo_dir.mkdir()

    # Initialize a clean synthetic git repository
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test Auditor",
        "GIT_AUTHOR_EMAIL": "auditor@repomedic.local",
        "GIT_COMMITTER_NAME": "Test Auditor",
        "GIT_COMMITTER_EMAIL": "auditor@repomedic.local",
    }

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Auditor"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "auditor@repomedic.local"], cwd=repo_dir, check=True, capture_output=True)

    # Commit 1: Introduce a secret file
    secret_file = repo_dir / "secret_config.py"
    raw_secret = "AKIAIOSFODNN7EXAMPLL"
    secret_file.write_text(f"AWS_KEY = '{raw_secret}'\n", encoding="utf-8")
    subprocess.run(["git", "add", "secret_config.py"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Commit with credential"], cwd=repo_dir, env=env, check=True, capture_output=True)

    # Commit 2: Remove the secret file (clean working tree)
    secret_file.unlink()
    subprocess.run(["git", "add", "secret_config.py"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Purge credential from working tree"], cwd=repo_dir, env=env, check=True, capture_output=True)

    # Verify working tree has NO secret_config.py
    assert not (repo_dir / "secret_config.py").exists()

    # Run GitHistoryScanner
    scanner = GitHistoryScanner(enabled=True, max_commits=10)
    findings, health = scanner.scan(repo_dir)

    assert health.status == ScannerStatus.COMPLETED
    assert len(findings) == 1

    f = findings[0]
    assert f.source == "git_history"
    assert f.rule_id == "GIT_SECRET_AWS_ACCESS_KEY"
    assert f.file_path == "secret_config.py"
    assert "Historical Secret in Git Commit" in f.title
    # Verify raw secret was redacted
    assert raw_secret not in f.evidence
    assert "[REDACTED]" in f.evidence

    # Verify repository was not modified (read-only guarantee)
    status_res = subprocess.run(["git", "status", "--porcelain"], cwd=repo_dir, capture_output=True, text=True)
    assert status_res.stdout.strip() == ""
