"""Generates reproducible, synthetic benchmark fixtures and ground-truth metadata."""

import json
from pathlib import Path

BENCHMARKS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = BENCHMARKS_DIR / "fixtures"
GROUND_TRUTH_DIR = BENCHMARKS_DIR / "ground_truth"

FIXTURE_SPECS = [
    {
        "id": "fix-01-aws-secret",
        "name": "Hardcoded Synthetic AWS Key",
        "description": "Python configuration file containing a hardcoded synthetic AWS Access Key ID.",
        "is_negative_control": False,
        "files": {
            "config.py": (
                "# Application Configuration\n"
                "AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLL'\n"
                "REGION = 'us-east-1'\n"
            )
        },
        "expected_findings": [
            {
                "category": "secret",
                "rule_id": "SECRET_AWS_ACCESS_KEY",
                "file_path": "config.py",
                "approximate_line": 2,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-02-github-pat",
        "name": "Hardcoded Synthetic GitHub PAT",
        "description": "Deployment script embedding a synthetic GitHub personal access token.",
        "is_negative_control": False,
        "files": {
            "deploy.py": (
                "# Deployment automation\n"
                "GITHUB_TOKEN = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'\n"
                "REPO = 'owner/repo'\n"
            )
        },
        "expected_findings": [
            {
                "category": "secret",
                "rule_id": "SECRET_GITHUB_PAT",
                "file_path": "deploy.py",
                "approximate_line": 2,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-03-db-uri",
        "name": "Database URI with Hardcoded Password",
        "description": "Database connection script embedding raw database credentials.",
        "is_negative_control": False,
        "files": {
            "database.py": (
                "# Database setup\n"
                "DB_URL = 'postgres://app_user:S3cur3Password123!@db.internal.net:5432/production'\n"
                "POOL_SIZE = 10\n"
            )
        },
        "expected_findings": [
            {
                "category": "secret",
                "rule_id": "SECRET_DB_URI",
                "file_path": "database.py",
                "approximate_line": 2,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-04-private-key",
        "name": "Private Key PEM Block",
        "description": "Certificate storage containing raw RSA private key block.",
        "is_negative_control": False,
        "files": {
            "server.pem": (
                "-----BEGIN RSA PRIVATE KEY-----\n"
                "MIIEowIBAAKCAQEA0m4wT3k0Zf6P+fVqF9kE5lB1c7e9qY0a3\n"
                "-----END RSA PRIVATE KEY-----\n"
            )
        },
        "expected_findings": [
            {
                "category": "secret",
                "rule_id": "SECRET_PRIVATE_KEY_BLOCK",
                "file_path": "server.pem",
                "approximate_line": 1,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-05-subprocess-shell",
        "name": "Subprocess Shell True",
        "description": "Task runner executing commands via shell=True enabling command injection.",
        "is_negative_control": False,
        "files": {
            "tasks.py": (
                "import subprocess\n\n"
                "def run_command(user_input):\n"
                "    subprocess.call(user_input, shell=True)\n"
            )
        },
        "expected_findings": [
            {
                "category": "subprocess_shell",
                "rule_id": "AST_SUBPROCESS_SHELL",
                "file_path": "tasks.py",
                "approximate_line": 4,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-06-sqli-fstring",
        "name": "SQL Injection via String Formatting",
        "description": "Database query executed using an f-string instead of parameterized inputs.",
        "is_negative_control": False,
        "files": {
            "repo.py": (
                "def get_user(cursor, user_id):\n"
                "    query = f\"SELECT * FROM users WHERE id = {user_id}\"\n"
                "    cursor.execute(query)\n"
            )
        },
        "expected_findings": [
            {
                "category": "sql_injection",
                "rule_id": "sql_string_building",
                "file_path": "repo.py",
                "approximate_line": 3,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-07-pickle-loads",
        "name": "Insecure Deserialization via Pickle",
        "description": "Unpickling untrusted payload data directly.",
        "is_negative_control": False,
        "files": {
            "cache.py": (
                "import pickle\n\n"
                "def load_cache(data):\n"
                "    return pickle.loads(data)\n"
            )
        },
        "expected_findings": [
            {
                "category": "unsafe_deserialization",
                "rule_id": "AST_PICKLE_UNSAFE",
                "file_path": "cache.py",
                "approximate_line": 4,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-08-yaml-load",
        "name": "Insecure YAML Load",
        "description": "Parsing YAML with yaml.load without specifying a safe Loader.",
        "is_negative_control": False,
        "files": {
            "loader.py": (
                "import yaml\n\n"
                "def load_spec(content):\n"
                "    return yaml.load(content)\n"
            )
        },
        "expected_findings": [
            {
                "category": "unsafe_yaml_load",
                "rule_id": "AST_YAML_UNSAFE",
                "file_path": "loader.py",
                "approximate_line": 4,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-09-alias-os-system",
        "name": "Aliased Import for os.system",
        "description": "Evading simple name matching by importing os.system as sys_exec.",
        "is_negative_control": False,
        "files": {
            "runner.py": (
                "from os import system as sys_exec\n\n"
                "def execute(cmd):\n"
                "    sys_exec(cmd)\n"
            )
        },
        "expected_findings": [
            {
                "category": "dangerous_os_call",
                "rule_id": "AST_OS_SYSTEM",
                "file_path": "runner.py",
                "approximate_line": 4,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-10-alias-subprocess",
        "name": "Aliased Subprocess Module Call",
        "description": "Subprocess module imported as sp and invoked with shell=True.",
        "is_negative_control": False,
        "files": {
            "worker.py": (
                "import subprocess as sp\n\n"
                "def do_work(cmd):\n"
                "    sp.run(cmd, shell=True)\n"
            )
        },
        "expected_findings": [
            {
                "category": "subprocess_shell",
                "rule_id": "AST_SUBPROCESS_SHELL",
                "file_path": "worker.py",
                "approximate_line": 4,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-11-tls-disabled",
        "name": "TLS Certificate Verification Disabled",
        "description": "HTTP request with verify=False disabling certificate checks.",
        "is_negative_control": False,
        "files": {
            "client.py": (
                "import requests\n\n"
                "def fetch(url):\n"
                "    return requests.get(url, verify=False)\n"
            )
        },
        "expected_findings": [
            {
                "category": "insecure_tls",
                "rule_id": "tls_verification_off",
                "file_path": "client.py",
                "approximate_line": 4,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-12-flask-debug",
        "name": "Framework Debug Mode Enabled",
        "description": "Flask app running with debug=True which exposes interactive debugger.",
        "is_negative_control": False,
        "files": {
            "app.py": (
                "from flask import Flask\n"
                "app = Flask(__name__)\n\n"
                "if __name__ == '__main__':\n"
                "    app.run(host='0.0.0.0', debug=True)\n"
            )
        },
        "expected_findings": [
            {
                "category": "debug_mode_enabled",
                "rule_id": "debug_mode_enabled",
                "file_path": "app.py",
                "approximate_line": 5,
                "severity": "medium",
            }
        ],
    },
    {
        "id": "fix-13-weak-hash",
        "name": "Weak Hash Algorithm (MD5)",
        "description": "Use of MD5 for hashing sensitive data.",
        "is_negative_control": False,
        "files": {
            "auth.py": (
                "import hashlib\n\n"
                "def hash_password(pwd):\n"
                "    return hashlib.md5(pwd.encode()).hexdigest()\n"
            )
        },
        "expected_findings": [
            {
                "category": "weak_hash",
                "rule_id": "weak_hash",
                "file_path": "auth.py",
                "approximate_line": 4,
                "severity": "medium",
            }
        ],
    },
    {
        "id": "fix-14-eval-injection",
        "name": "JavaScript Dynamic Eval Injection",
        "description": "Direct dynamic code execution via JavaScript eval().",
        "is_negative_control": False,
        "files": {
            "calc.js": (
                "function evaluateExpression(input) {\n"
                "    return eval(input);\n"
                "}\n"
            )
        },
        "expected_findings": [
            {
                "category": "js_eval",
                "rule_id": "js_eval",
                "file_path": "calc.js",
                "approximate_line": 2,
                "severity": "high",
            }
        ],
    },
    {
        "id": "fix-15-clean-python-app",
        "name": "Clean Python Utility (Negative Control)",
        "description": "Secure Python code adhering to best practices; zero vulnerabilities expected.",
        "is_negative_control": True,
        "files": {
            "safe_service.py": (
                "import hashlib\n"
                "import subprocess\n\n"
                "def hash_data(data: bytes) -> str:\n"
                "    return hashlib.sha256(data).hexdigest()\n\n"
                "def list_files(path: str) -> None:\n"
                "    subprocess.run(['ls', '-la', path], shell=False, check=True)\n"
            )
        },
        "expected_findings": [],
    },
    {
        "id": "fix-16-clean-config-util",
        "name": "Clean Configuration Utility (Negative Control)",
        "description": "Safe configuration reading environment variables without credentials.",
        "is_negative_control": True,
        "files": {
            "settings.py": (
                "import os\n\n"
                "PORT = int(os.environ.get('PORT', 8000))\n"
                "APP_ENV = os.environ.get('ENV', 'development')\n"
                "TIMEOUT = 30\n"
            )
        },
        "expected_findings": [],
    },
]


def generate_fixtures() -> None:
    """Populates all synthetic fixture directories and ground truth JSON files."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    for spec in FIXTURE_SPECS:
        fid = spec["id"]
        fixture_path = FIXTURES_DIR / fid
        fixture_path.mkdir(parents=True, exist_ok=True)

        # Write fixture files
        for filename, content in spec["files"].items():
            filepath = fixture_path / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding="utf-8")

        # Write ground-truth metadata
        gt_metadata = {
            "fixture_id": fid,
            "name": spec["name"],
            "description": spec["description"],
            "is_negative_control": spec["is_negative_control"],
            "expected_findings": spec["expected_findings"],
        }
        gt_file = GROUND_TRUTH_DIR / f"{fid}.json"
        gt_file.write_text(json.dumps(gt_metadata, indent=2), encoding="utf-8")

    print(f"Successfully generated {len(FIXTURE_SPECS)} benchmark fixtures and ground-truth specs.")


if __name__ == "__main__":
    generate_fixtures()
