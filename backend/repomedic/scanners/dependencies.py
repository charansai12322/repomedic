"""Dependency manifest discovery and OSV.dev vulnerability lookup (Fixes AUDIT-004, AUDIT-005, AUDIT-009)."""

from concurrent.futures import ThreadPoolExecutor
import fnmatch
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import requests
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity
from repomedic.models.health import ScannerHealth, ScannerStatus
from repomedic.scanners.base import BaseScanner


SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
    "vendor", "site-packages", ".tox", ".mypy_cache"
}

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_VULN_URL = "https://api.osv.dev/v1/vulns/"
MAX_DEPENDENCY_QUERIES = 100
MAX_VULN_DETAIL_QUERIES = 40


def parse_requirements_file(file_path: Path, repo_dir: Path) -> List[Dict[str, str]]:
    """Parses requirements.txt supporting exact pins, version ranges, comments, and extras (Fixes AUDIT-005)."""
    packages = []
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    rel_source = str(file_path.relative_to(repo_dir)).replace("\\", "/")

    for raw_line in lines:
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        # Strip environment markers (e.g. ; python_version >= '3.8')
        line = line.split(";", 1)[0].strip()
        # Strip extras (e.g. requests[security] -> requests)
        line = re.sub(r"\[.*?\]", "", line)

        # 1. Exact match (==)
        m_exact = re.match(r"^([A-Za-z0-9_.-]+)\s*==\s*([A-Za-z0-9_.+!:-]+)", line)
        if m_exact:
            packages.append({
                "name": m_exact.group(1),
                "version": m_exact.group(2),
                "ecosystem": "PyPI",
                "source": rel_source
            })
            continue

        # 2. Minimum range (>=, ~=) - take minimum specified version for vulnerability lower bound check
        m_range = re.match(r"^([A-Za-z0-9_.-]+)\s*(?:>=|~=)\s*([A-Za-z0-9_.+!:-]+)", line)
        if m_range:
            packages.append({
                "name": m_range.group(1),
                "version": m_range.group(2),
                "ecosystem": "PyPI",
                "source": rel_source
            })

    return packages


def parse_package_lock_file(file_path: Path, repo_dir: Path) -> List[Dict[str, str]]:
    """Parses npm package-lock.json supporting both v2/v3 packages and v1 dependencies (Fixes AUDIT-005)."""
    if file_path.stat().st_size > 4_000_000:
        return []

    try:
        lock = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    rel_source = str(file_path.relative_to(repo_dir)).replace("\\", "/")
    packages = []

    # Format v2 and v3: lock.get("packages")
    if "packages" in lock and isinstance(lock["packages"], dict):
        for pkg_path, data in lock["packages"].items():
            if not isinstance(data, dict):
                continue
            if "node_modules/" not in pkg_path:
                continue
            name = pkg_path.rsplit("node_modules/", 1)[-1]
            version = data.get("version")
            if name and version:
                packages.append({
                    "name": name,
                    "version": str(version),
                    "ecosystem": "npm",
                    "source": rel_source
                })

    # Format v1 fallback: lock.get("dependencies")
    elif "dependencies" in lock and isinstance(lock["dependencies"], dict):
        for name, data in lock["dependencies"].items():
            if isinstance(data, dict):
                version = data.get("version")
                if version and not str(version).startswith("http"):
                    packages.append({
                        "name": name,
                        "version": str(version),
                        "ecosystem": "npm",
                        "source": rel_source
                    })

    return packages


def parse_pyproject_toml_file(file_path: Path, repo_dir: Path) -> List[Dict[str, str]]:
    """Lightweight extractor for dependencies in pyproject.toml."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    rel_source = str(file_path.relative_to(repo_dir)).replace("\\", "/")
    packages = []

    # Simple regex for dependencies in standard pyproject.toml format
    for m in re.finditer(r'["\']([A-Za-z0-9_.-]+)\s*(?:==|>=)\s*([0-9A-Za-z_.+!:-]+)["\']', content):
        packages.append({
            "name": m.group(1),
            "version": m.group(2),
            "ecosystem": "PyPI",
            "source": rel_source
        })

    return packages


def extract_osv_severity(detail: Dict[str, Any]) -> Severity:
    """
    Extracts standardized severity from OSV detail, evaluating database_specific severity
    or falling back to CVSS vector scores (Fixes AUDIT-009).
    """
    db_sev = ((detail.get("database_specific") or {}).get("severity") or "").upper()
    mapping = {
        "CRITICAL": Severity.CRITICAL,
        "HIGH": Severity.HIGH,
        "MODERATE": Severity.MEDIUM,
        "MEDIUM": Severity.MEDIUM,
        "LOW": Severity.LOW,
    }
    if db_sev in mapping:
        return mapping[db_sev]

    # CVSS vector inspection fallback
    severities = detail.get("severity") or []
    for s_entry in severities:
        score_str = s_entry.get("score", "")
        # Strip out CVSS version prefix (e.g. CVSS:3.1/ or CVSS:3.0/) so it doesn't match as a 3.1 score
        score_clean = re.sub(r"CVSS:[0-9.]+/?", "", score_str, flags=re.I)
        # Look for explicit base scores (e.g. 9.8, 7.5, 10.0)
        m = re.search(r"\b([0-9]\.[0-9]|10\.0)\b", score_clean)
        if m:
            try:
                cvss_num = float(m.group(1))
                if cvss_num >= 9.0:
                    return Severity.CRITICAL
                elif cvss_num >= 7.0:
                    return Severity.HIGH
                elif cvss_num >= 4.0:
                    return Severity.MEDIUM
                else:
                    return Severity.LOW
            except ValueError:
                pass

    return Severity.MEDIUM


class DependencyScanner(BaseScanner):
    """Dependency vulnerability scanner leveraging the public OSV.dev distributed database."""

    def __init__(self, required: bool = True, timeout_seconds: int = 25):
        super().__init__(name="osv", required=required)
        self.timeout_seconds = timeout_seconds

    def scan(self, repo_dir: Path) -> Tuple[List[Finding], ScannerHealth]:
        t0 = time.time()
        deps: List[Dict[str, str]] = []

        try:
            # 1. Discover manifests recursively across the entire repository (monorepos included)
            for root, dirs, files in os.walk(repo_dir):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for name in files:
                    file_path = Path(root) / name
                    if file_path.is_symlink():
                        continue
                    if fnmatch.fnmatch(name.lower(), "*requirements*.txt"):
                        deps.extend(parse_requirements_file(file_path, repo_dir))
                    elif name.lower() == "package-lock.json":
                        deps.extend(parse_package_lock_file(file_path, repo_dir))
                    elif name.lower() == "pyproject.toml":
                        deps.extend(parse_pyproject_toml_file(file_path, repo_dir))

            # Deduplicate discovered coordinates
            unique_deps_map: Dict[Tuple[str, str, str], Dict[str, str]] = {}
            for d in deps:
                key = (d["ecosystem"], d["name"].lower(), d["version"])
                unique_deps_map[key] = d

            unique_deps = list(unique_deps_map.values())[:MAX_DEPENDENCY_QUERIES]

            if not unique_deps:
                duration_ms = int((time.time() - t0) * 1000)
                return [], ScannerHealth(
                    status=ScannerStatus.COMPLETED,
                    required=self.required,
                    duration_ms=duration_ms,
                    finding_count=0
                )

            # 2. Batch query OSV API
            queries = [
                {"package": {"name": d["name"], "ecosystem": d["ecosystem"]}, "version": d["version"]}
                for d in unique_deps
            ]

            try:
                resp = requests.post(
                    OSV_BATCH_URL,
                    json={"queries": queries},
                    timeout=self.timeout_seconds
                )
                resp.raise_for_status()
                batch_results = resp.json().get("results", [])
            except requests.RequestException as e:
                duration_ms = int((time.time() - t0) * 1000)
                return [], ScannerHealth(
                    status=ScannerStatus.FAILED,
                    required=self.required,
                    duration_ms=duration_ms,
                    error_code="OSV_API_UNAVAILABLE",
                    error_message=f"OSV batch lookup failed: {str(e)[:160]}",
                    finding_count=0
                )

            # 3. Associate vulnerabilities with dependencies
            pairs: List[Tuple[Dict[str, str], str]] = []
            for dep, res in zip(unique_deps, batch_results):
                vulns = res.get("vulns") or []
                for v in vulns[:10]:
                    vid = v.get("id")
                    if vid:
                        pairs.append((dep, vid))

            if not pairs:
                duration_ms = int((time.time() - t0) * 1000)
                return [], ScannerHealth(
                    status=ScannerStatus.COMPLETED,
                    required=self.required,
                    duration_ms=duration_ms,
                    finding_count=0
                )

            # 4. Enrich details concurrently (up to 40 unique IDs)
            unique_vids = list(dict.fromkeys(vid for _, vid in pairs))[:MAX_VULN_DETAIL_QUERIES]

            def fetch_detail(vid: str) -> Tuple[str, Dict[str, Any]]:
                try:
                    r = requests.get(OSV_VULN_URL + vid, timeout=8)
                    r.raise_for_status()
                    return vid, r.json()
                except Exception:
                    return vid, {}

            details_map: Dict[str, Dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=6) as executor:
                for vid, data in executor.map(fetch_detail, unique_vids):
                    details_map[vid] = data

            # 5. Build canonical findings
            findings: List[Finding] = []
            for dep, vid in pairs:
                detail = details_map.get(vid, {})
                severity = extract_osv_severity(detail)
                summary = (detail.get("summary") or "").strip()
                desc = f"Known dependency vulnerability {vid} affects {dep['name']} {dep['version']}."
                if summary:
                    desc += f" {summary[:160]}"

                rule_id = f"osv:{vid}:{dep['name'].lower()}"
                fid = hashlib.sha1(f"{rule_id}|{dep['source']}|1".encode("utf-8")).hexdigest()[:10]

                findings.append(
                    Finding(
                        id=f"F-{fid}",
                        title=f"Vulnerable Dependency: {dep['name']} ({vid})",
                        description=desc,
                        severity=severity,
                        confidence=Confidence.HIGH,
                        source="osv",
                        evidence_quality=EvidenceQuality.DETERMINISTIC,
                        rule_id=rule_id,
                        file_path=dep["source"],
                        line_start=1,
                        line_end=1,
                        evidence=f"{dep['name']}=={dep['version']}",
                        remediation=f"Upgrade {dep['name']} to a secure version in {dep['source']}.",
                        references=[f"https://osv.dev/vulnerability/{vid}"]
                    )
                )

            duration_ms = int((time.time() - t0) * 1000)
            return findings, ScannerHealth(
                status=ScannerStatus.COMPLETED,
                required=self.required,
                duration_ms=duration_ms,
                finding_count=len(findings)
            )

        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            return [], ScannerHealth(
                status=ScannerStatus.FAILED,
                required=self.required,
                duration_ms=duration_ms,
                error_code="DEPENDENCY_SCANNER_ERROR",
                error_message=str(e)[:200],
                finding_count=0
            )
