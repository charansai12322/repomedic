"""Security and reliability tests for git cloning and git history scanning."""

from pathlib import Path
import subprocess
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from repomedic.exceptions import ScanError
from repomedic.services.scan_service import ScanService, safe_cleanup_dir


def test_hardened_clone_preserves_git_dir_when_git_history_enabled():
    """When git history scanning is explicitly enabled, .git must be preserved for log inspection."""
    service = ScanService()

    # Mock subprocess.run to simulate successful git clone into dest
    def mock_clone(cmd, *args, **kwargs):
        dest_dir = Path(cmd[-1])
        dest_dir.mkdir(parents=True, exist_ok=True)
        # Create fake .git folder
        (dest_dir / ".git").mkdir(parents=True, exist_ok=True)
        (dest_dir / "app.py").write_text("print('hello')", encoding="utf-8")
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=mock_clone):
        dest, root = service._hardened_clone("https://github.com/owner/repo.git", enable_git_history=True)
        try:
            assert (dest / ".git").exists(), ".git folder must be preserved when enable_git_history=True"
            assert (dest / "app.py").exists()
        finally:
            safe_cleanup_dir(root)


def test_hardened_clone_strips_git_dir_when_git_history_disabled():
    """When git history scanning is disabled, .git must be stripped as a defense-in-depth measure."""
    service = ScanService()

    def mock_clone(cmd, *args, **kwargs):
        dest_dir = Path(cmd[-1])
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / ".git").mkdir(parents=True, exist_ok=True)
        (dest_dir / "app.py").write_text("print('hello')", encoding="utf-8")
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=mock_clone):
        dest, root = service._hardened_clone("https://github.com/owner/repo.git", enable_git_history=False)
        try:
            assert not (dest / ".git").exists(), ".git folder must be stripped when enable_git_history=False"
            assert (dest / "app.py").exists()
        finally:
            safe_cleanup_dir(root)


def test_hardened_clone_cleans_up_on_failure():
    """Temporary root folder must be cleaned up if git clone fails."""
    service = ScanService()

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["git", "clone"], stderr="Clone error")):
        with pytest.raises(ScanError):
            service._hardened_clone("https://github.com/owner/repo.git")
