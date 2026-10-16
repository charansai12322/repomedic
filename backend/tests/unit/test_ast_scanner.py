"""Tests for Python AST scanner and alias-aware import resolution (Fixes AUDIT-002)."""

from pathlib import Path
from repomedic.scanners.python_ast import PythonASTScanner


def test_ast_detects_standard_calls(temp_repo_dir: Path):
    """Detects direct standard calls to dangerous functions."""
    code = """
import os, pickle, subprocess

os.system("echo hello")
pickle.loads(b"data")
subprocess.run("ls", shell=True)
eval("1 + 1")
exec("x = 2")
"""
    (temp_repo_dir / "app.py").write_text(code, encoding="utf-8")
    scanner = PythonASTScanner()
    findings, health = scanner.scan(temp_repo_dir)

    rule_ids = {f.rule_id for f in findings}
    assert "py_os_system" in rule_ids
    assert "py_unsafe_deserialization" in rule_ids
    assert "py_subprocess_shell" in rule_ids
    assert "py_eval_exec" in rule_ids
    assert health.status.value == "completed"


def test_ast_detects_from_import_aliasing(temp_repo_dir: Path):
    """Verifies that 'from os import system' and 'from pickle import loads' are detected (Fixes AUDIT-002)."""
    code = """
from os import system
from pickle import loads
from subprocess import Popen

system("whoami")
loads(b"malicious_payload")
Popen("rm -rf /", shell=True)
"""
    (temp_repo_dir / "evasion.py").write_text(code, encoding="utf-8")
    scanner = PythonASTScanner()
    findings, health = scanner.scan(temp_repo_dir)

    rule_ids = {f.rule_id for f in findings}
    assert "py_os_system" in rule_ids, "Failed to detect 'from os import system'"
    assert "py_unsafe_deserialization" in rule_ids, "Failed to detect 'from pickle import loads'"
    assert "py_subprocess_shell" in rule_ids, "Failed to detect 'from subprocess import Popen(shell=True)'"


def test_ast_detects_module_as_aliasing(temp_repo_dir: Path):
    """Verifies that 'import pickle as p' and 'import subprocess as sp' are detected (Fixes AUDIT-002)."""
    code = """
import pickle as p
import subprocess as sp
import os as operating_system

p.loads(b"test")
sp.run(["echo", "safe"], shell=True)
operating_system.system("id")
"""
    (temp_repo_dir / "alias.py").write_text(code, encoding="utf-8")
    scanner = PythonASTScanner()
    findings, health = scanner.scan(temp_repo_dir)

    rule_ids = {f.rule_id for f in findings}
    assert "py_unsafe_deserialization" in rule_ids
    assert "py_subprocess_shell" in rule_ids
    assert "py_os_system" in rule_ids


def test_ast_detects_yaml_unsafe_load(temp_repo_dir: Path):
    """Detects yaml.load without safe loader, but ignores yaml.safe_load."""
    code = """
import yaml
from yaml import load

cfg1 = yaml.load(data)
cfg2 = load(data)
cfg3 = yaml.safe_load(data)
"""
    (temp_repo_dir / "config.py").write_text(code, encoding="utf-8")
    scanner = PythonASTScanner()
    findings, health = scanner.scan(temp_repo_dir)

    yaml_findings = [f for f in findings if f.rule_id == "py_yaml_unsafe_load"]
    assert len(yaml_findings) == 2, f"Expected 2 yaml.load findings, found {len(yaml_findings)}"


def test_ast_safe_code_produces_zero_findings(temp_repo_dir: Path):
    """Safe, idiomatic Python code must produce zero findings."""
    code = """
import json
import subprocess

def add(a, b):
    return a + b

def run_ls():
    return subprocess.run(["ls", "-la"], shell=False, check=True)

data = json.loads('{"key": "value"}')
"""
    (temp_repo_dir / "safe.py").write_text(code, encoding="utf-8")
    scanner = PythonASTScanner()
    findings, health = scanner.scan(temp_repo_dir)

    assert len(findings) == 0
    assert health.status.value == "completed"


def test_ast_handles_syntax_error_gracefully(temp_repo_dir: Path):
    """Files with Python 2 syntax or broken grammar should not crash the scanner."""
    code = "def broken(:\n    pass print 'hello'"
    (temp_repo_dir / "bad_syntax.py").write_text(code, encoding="utf-8")
    scanner = PythonASTScanner()
    findings, health = scanner.scan(temp_repo_dir)

    assert len(findings) == 0
    assert health.status.value == "completed"
