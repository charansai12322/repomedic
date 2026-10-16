"""Pytest configuration and shared test fixtures."""

import os
from pathlib import Path
import tempfile
import pytest

# Ensure testing runs in development mode without external key requirements
os.environ["REPOMEDIC_ENV"] = "development"
os.environ["REPOMEDIC_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""


@pytest.fixture
def temp_repo_dir():
    """Provides an isolated temporary directory simulating a repository tree."""
    with tempfile.TemporaryDirectory(prefix="test_repo_") as tmpdir:
        yield Path(tmpdir)
