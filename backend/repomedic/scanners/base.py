"""Abstract base scanner interface for RepoMedic."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple
from repomedic.models.findings import Finding
from repomedic.models.health import ScannerHealth


class BaseScanner(ABC):
    """Abstract base class for all deterministic security scanners."""

    def __init__(self, name: str, required: bool = True):
        self.name = name
        self.required = required

    @abstractmethod
    def scan(self, repo_dir: Path) -> Tuple[List[Finding], ScannerHealth]:
        """
        Executes scanner inspection on the local repository directory.
        Must return a tuple of (findings_list, scanner_health).
        Exceptions must be caught and returned as ScannerStatus.FAILED in ScannerHealth.
        """
        pass
