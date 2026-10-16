"""AI-assisted triage engine with schema enforcement and strict citation validation (Workstream 8)."""

from collections import Counter
import json
import re
import time
from typing import Any, Dict, List, Set, Tuple
from repomedic.config import settings
from repomedic.logging_config import get_logger
from repomedic.models.findings import EvidenceQuality, Finding, Severity
from repomedic.models.health import ScannerHealth, ScannerStatus
from repomedic.models.reports import AIDiagnosis, AITriageResult
from repomedic.ai.model_discovery import model_discovery
from repomedic.ai.prompts import SYSTEM_PROMPT, wrap_untrusted_snippet
from repomedic.ai.provider import groq_provider

logger = get_logger("ai.triage")

BASE_LIMITATIONS = [
    "Static analysis only: findings indicate security risks, not verified runtime exploitability.",
    "Only a prioritized subset of deterministic findings is submitted for AI evaluation.",
    "Source code snippets containing potential credentials are redacted prior to analysis.",
    "AI interpretations are contextual suggestions and must be verified by a human engineer."
]


def clean_json_response(raw: str) -> str:
    """Strips markdown code block markers and trims surrounding whitespace."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    s = cleaned.find("{")
    e = cleaned.rfind("}")
    return cleaned[s:e + 1] if s != -1 and e != -1 else cleaned


class AITriageEngine:
    """Executes LLM triage over deterministic findings, enforcing schema and citation validity."""

    def __init__(self, required: bool = False):
        self.required = required

    def select_findings_for_triage(self, findings: List[Finding]) -> List[Finding]:
        """Filters and prioritizes findings within token limits (skipping INFO, capping per rule)."""
        chosen: List[Finding] = []
        per_rule: Counter = Counter()

        for f in findings:
            if f.severity == Severity.INFO:
                continue
            rule_key = f.rule_id.split(":")[0] if f.rule_id.startswith("osv") else f.rule_id
            if per_rule[rule_key] >= settings.REPOMEDIC_MAX_PER_RULE_FOR_AI:
                continue
            per_rule[rule_key] += 1
            chosen.append(f)
            if len(chosen) >= settings.REPOMEDIC_MAX_AI_FINDINGS:
                break

        return chosen

    def triage(self, findings: List[Finding], repo_label: str) -> Tuple[AITriageResult, ScannerHealth]:
        t0 = time.time()
        active_model = model_discovery.get_active_model()

        # Handle zero findings cleanly
        if not findings:
            duration_ms = int((time.time() - t0) * 1000)
            return (
                AITriageResult(
                    executive_summary="No security findings were detected by deterministic scanners in this repository.",
                    diagnoses=[],
                    limitations=BASE_LIMITATIONS,
                    citation_validity_percent=100.0,
                    model="none",
                    mode="deterministic_only",
                    duration_ms=duration_ms
                ),
                ScannerHealth(
                    status=ScannerStatus.COMPLETED,
                    required=self.required,
                    duration_ms=duration_ms,
                    finding_count=0
                )
            )

        client = groq_provider.client
        # Deterministic-only fallback when Groq client is unconfigured
        if not client:
            duration_ms = int((time.time() - t0) * 1000)
            return (
                AITriageResult(
                    executive_summary=f"AI triage omitted (Groq API key not configured). Displaying {len(findings)} deterministic findings.",
                    diagnoses=[],
                    limitations=BASE_LIMITATIONS + ["AI triage was not executed for this run."],
                    citation_validity_percent=100.0,
                    model="none (offline)",
                    mode="deterministic_only",
                    duration_ms=duration_ms
                ),
                ScannerHealth(
                    status=ScannerStatus.SKIPPED,
                    required=self.required,
                    duration_ms=duration_ms,
                    error_code="GROQ_NOT_CONFIGURED",
                    error_message="Groq API key not configured; ran in deterministic-only mode.",
                    finding_count=0
                )
            )

        selected = self.select_findings_for_triage(findings)
        valid_finding_ids: Set[str] = {f.id for f in findings}

        # Build payload with safe XML snippet delimiters
        payload = {
            "repository": repo_label,
            "total_findings": len(findings),
            "findings": [
                {
                    "id": f.id,
                    "severity": f.severity.value,
                    "rule_id": f.rule_id,
                    "file_path": f.file_path,
                    "line": f.line_start,
                    "description": f.description,
                    "evidence": wrap_untrusted_snippet(f.evidence)
                }
                for f in selected
            ]
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)}
        ]

        triage_data: Optional[Dict[str, Any]] = None
        last_error: Optional[Exception] = None

        # Execute chat completion with up to 2 retries on schema errors
        for attempt in range(2):
            try:
                chat_resp = client.chat.completions.create(
                    model=active_model,
                    messages=messages,
                    temperature=0.2,
                    max_completion_tokens=4096,
                    response_format={"type": "json_object"}
                )
                raw_text = chat_resp.choices[0].message.content or "{}"
                cleaned_text = clean_json_response(raw_text)
                triage_data = json.loads(cleaned_text)
                break
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(f"AI response JSON parsing failed on attempt {attempt + 1}: {e}")
                messages.append({"role": "assistant", "content": raw_text or "{}"})
                messages.append({
                    "role": "user",
                    "content": f"Your response was not valid JSON ({str(e)[:120]}). Return ONLY a valid JSON object matching the requested schema."
                })
            except Exception as e:
                last_error = e
                logger.warning(f"Groq API call failed on attempt {attempt + 1}: {e}")
                time.sleep(1.0 * (attempt + 1))

        duration_ms = int((time.time() - t0) * 1000)

        # Fallback if inference failed
        if not triage_data:
            err_msg = f"AI triage failed: {type(last_error).__name__}"
            return (
                AITriageResult(
                    executive_summary=f"AI triage unavailable ({type(last_error).__name__}). Showing deterministic findings.",
                    diagnoses=[],
                    limitations=BASE_LIMITATIONS + ["AI inference failed during this scan."],
                    citation_validity_percent=0.0,
                    model=active_model,
                    mode="deterministic_only",
                    duration_ms=duration_ms
                ),
                ScannerHealth(
                    status=ScannerStatus.FAILED,
                    required=self.required,
                    duration_ms=duration_ms,
                    error_code="AI_INFERENCE_FAILED",
                    error_message=str(last_error)[:180],
                    finding_count=0
                )
            )

        # Enforce Citation Integrity: Drop any diagnosis referring to hallucinated finding IDs
        raw_diagnoses = triage_data.get("diagnoses", [])
        validated_diagnoses: List[AIDiagnosis] = []
        seen_ids: Set[str] = set()

        for item in raw_diagnoses:
            try:
                diag = AIDiagnosis(**item)
                # Verify that finding_id exists in the deterministic findings
                if diag.finding_id in valid_finding_ids and diag.finding_id not in seen_ids:
                    seen_ids.add(diag.finding_id)
                    validated_diagnoses.append(diag)
                else:
                    logger.warning(f"Dropped invalid/hallucinated AI citation: {diag.finding_id}")
            except Exception as e:
                logger.warning(f"Dropped malformed diagnosis item: {e}")

        total_proposed = len(raw_diagnoses)
        validity_pct = 100.0 if total_proposed == 0 else round(100.0 * len(validated_diagnoses) / total_proposed, 1)

        # Sort diagnoses by priority (1 to 5)
        validated_diagnoses.sort(key=lambda d: d.priority)

        parsed_limitations = triage_data.get("limitations", [])
        if not isinstance(parsed_limitations, list):
            parsed_limitations = []
        merged_limitations = list(dict.fromkeys(BASE_LIMITATIONS + [str(x) for x in parsed_limitations]))[:8]

        result = AITriageResult(
            executive_summary=str(triage_data.get("executive_summary", "")).strip(),
            diagnoses=validated_diagnoses,
            limitations=merged_limitations,
            citation_validity_percent=validity_pct,
            model=active_model,
            mode="groq",
            duration_ms=duration_ms
        )

        health = ScannerHealth(
            status=ScannerStatus.COMPLETED,
            required=self.required,
            duration_ms=duration_ms,
            finding_count=len(validated_diagnoses)
        )
        return result, health
