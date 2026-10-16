"""Tests for SSRF prevention and repository URL validation."""

import pytest
from repomedic.exceptions import InvalidTargetError
from repomedic.services.scan_service import validate_repository_url


def test_valid_github_urls_accepted():
    assert validate_repository_url("https://github.com/OWASP/NodeGoat") == "https://github.com/OWASP/NodeGoat.git"
    assert validate_repository_url("https://github.com/pallets/flask.git") == "https://github.com/pallets/flask.git"
    assert validate_repository_url("https://github.com/my-org/repo_name.git/") == "https://github.com/my-org/repo_name.git"


def test_ssrf_local_and_private_network_rejected():
    with pytest.raises(InvalidTargetError):
        validate_repository_url("http://localhost:8000/repo")

    with pytest.raises(InvalidTargetError):
        validate_repository_url("https://127.0.0.1/admin/repo")

    with pytest.raises(InvalidTargetError):
        validate_repository_url("https://169.254.169.254/latest/meta-data")

    with pytest.raises(InvalidTargetError):
        validate_repository_url("https://10.0.0.5/internal/repo")

    with pytest.raises(InvalidTargetError):
        validate_repository_url("https://192.168.1.1/secret/repo")


def test_ssrf_credential_stuffing_rejected():
    with pytest.raises(InvalidTargetError):
        validate_repository_url("https://admin:password@evil.com/repo")


def test_non_github_schemes_and_hosts_rejected():
    with pytest.raises(InvalidTargetError):
        validate_repository_url("file:///etc/passwd")

    with pytest.raises(InvalidTargetError):
        validate_repository_url("ftp://ftp.example.com/repo")

    with pytest.raises(InvalidTargetError):
        validate_repository_url("https://gitlab.com/owner/repo")

    with pytest.raises(InvalidTargetError):
        validate_repository_url("https://bitbucket.org/owner/repo")

    with pytest.raises(InvalidTargetError):
        validate_repository_url("https://github.com/a/b; rm -rf /")
