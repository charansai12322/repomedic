"""Standalone HTML report exporter for RepoMedic."""

import html
from repomedic.models.findings import Severity
from repomedic.models.health import AuditStatus, ScannerStatus
from repomedic.models.reports import ScanReport


def export_report_to_html(report: ScanReport) -> str:
    """Generates a standalone, beautiful HTML audit report with sanitized evidence."""
    target_esc = html.escape(report.target)
    start_time = html.escape(report.scan_health.start_time or "N/A")
    finish_time = html.escape(report.scan_health.finish_time or "N/A")
    duration_s = f"{report.scan_health.total_duration_ms / 1000.0:.2f}s"
    
    # Audit status badge styling
    if report.partial_audit:
        status_badge = '<span class="badge badge-warning">PARTIAL AUDIT (Required Scanner Failed/Unavailable)</span>'
    elif report.audit_status == AuditStatus.COMPLETE:
        status_badge = '<span class="badge badge-success">COMPLETE AUDIT</span>'
    else:
        status_badge = '<span class="badge badge-danger">FAILED AUDIT</span>'

    # Score color
    grade = html.escape(report.score.grade)
    score_val = report.score.score
    grade_color = "#10b981" if score_val >= 80 else ("#f59e0b" if score_val >= 60 else "#ef4444")

    # Scanner health rows
    health_rows = []
    for s_name, s_h in report.scan_health.scanners.items():
        name_esc = html.escape(s_name)
        status_str = s_h.status.value.upper()
        badge_cls = (
            "badge-success" if s_h.status == ScannerStatus.COMPLETED
            else ("badge-warning" if s_h.status in (ScannerStatus.SKIPPED, ScannerStatus.UNAVAILABLE)
            else "badge-danger")
        )
        req_str = "Yes" if s_h.required else "No"
        diag_msg = html.escape(s_h.diagnostic_message or "")
        health_rows.append(f"""
        <tr>
            <td><strong>{name_esc}</strong></td>
            <td><span class="badge {badge_cls}">{status_str}</span></td>
            <td>{req_str}</td>
            <td>{s_h.duration_ms} ms</td>
            <td>{s_h.finding_count}</td>
            <td><small class="text-muted">{diag_msg}</small></td>
        </tr>
        """)
    health_table_body = "\n".join(health_rows)

    # Findings rows
    findings = report.evidence.findings
    if not findings:
        findings_html = """
        <div class="empty-state">
            <h3>No security findings detected!</h3>
            <p>None of the active scanners identified actionable security vulnerabilities in the inspected files.</p>
        </div>
        """
    else:
        finding_cards = []
        for f in findings:
            sev_cls = f"sev-{f.severity.value.lower()}"
            sev_badge = f'<span class="badge {sev_cls}">{html.escape(f.severity.value.upper())}</span>'
            evidence_block = ""
            if f.evidence:
                evidence_block = f"""
                <div class="evidence-box">
                    <div class="evidence-header">Evidence (Sanitized & Secrets Redacted)</div>
                    <pre><code>{html.escape(f.evidence)}</code></pre>
                </div>
                """
            remediation_block = ""
            if f.remediation:
                remediation_block = f"""
                <div class="remediation-box">
                    <strong>Remediation:</strong> {html.escape(f.remediation)}
                </div>
                """
            finding_cards.append(f"""
            <div class="finding-card">
                <div class="finding-top">
                    <div>
                        {sev_badge}
                        <strong class="finding-title">{html.escape(f.title)}</strong>
                    </div>
                    <span class="finding-source">{html.escape(f.source)} | {html.escape(f.rule_id)}</span>
                </div>
                <p class="finding-desc">{html.escape(f.description)}</p>
                <div class="finding-location">
                    <code>{html.escape(f.file_path)}:{f.line_start}</code>
                    <span class="meta-tag">Confidence: {html.escape(f.confidence.value)}</span>
                    <span class="meta-tag">Quality: {html.escape(f.evidence_quality.value)}</span>
                </div>
                {evidence_block}
                {remediation_block}
            </div>
            """)
        findings_html = "\n".join(finding_cards)

    # Executive Summary / AI triage
    ai = report.ai_triage
    summary_html = html.escape(ai.executive_summary)
    ai_mode_badge = f'<span class="badge badge-info">{html.escape(ai.mode.upper())}</span>'
    ai_model = html.escape(ai.model)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RepoMedic Security Audit — {target_esc}</title>
    <style>
        :root {{
            --bg: #090d16;
            --surface: #111827;
            --border: #1f2937;
            --text: #f3f4f6;
            --muted: #9ca3af;
            --primary: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #06b6d4;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 32px 16px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
        h2 {{ margin-top: 32px; margin-bottom: 16px; font-size: 18px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        .badge-success {{ background: rgba(16,185,129,0.2); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }}
        .badge-warning {{ background: rgba(245,158,11,0.2); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }}
        .badge-danger {{ background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }}
        .badge-info {{ background: rgba(6,182,212,0.2); color: #38bdf8; border: 1px solid rgba(6,182,212,0.3); }}
        .sev-critical {{ background: #7f1d1d; color: #fca5a5; }}
        .sev-high {{ background: #991b1b; color: #fecaca; }}
        .sev-medium {{ background: #92400e; color: #fde68a; }}
        .sev-low {{ background: #1e3a8a; color: #bfdbfe; }}
        .sev-info {{ background: #374151; color: #e5e7eb; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }}
        .card-label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; font-weight: 600; }}
        .card-value {{ font-size: 28px; font-weight: 800; margin-top: 4px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 13px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{ color: var(--muted); font-size: 11px; text-transform: uppercase; }}
        .finding-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        .finding-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }}
        .finding-title {{ margin-left: 8px; font-size: 15px; }}
        .finding-source {{ font-size: 12px; color: var(--muted); }}
        .finding-desc {{ font-size: 13px; color: #d1d5db; margin: 8px 0; }}
        .finding-location {{ font-size: 12px; color: var(--muted); margin-bottom: 12px; display: flex; gap: 8px; align-items: center; }}
        .meta-tag {{ background: #1f2937; padding: 2px 6px; border-radius: 4px; font-size: 11px; }}
        .evidence-box {{
            background: #030712;
            border: 1px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
            margin: 12px 0;
        }}
        .evidence-header {{
            background: #111827;
            padding: 6px 12px;
            font-size: 11px;
            color: var(--muted);
            border-bottom: 1px solid var(--border);
        }}
        pre {{ margin: 0; padding: 12px; font-size: 12px; font-family: monospace; overflow-x: auto; color: #a5b4fc; }}
        .remediation-box {{
            background: rgba(16,185,129,0.1);
            border-left: 3px solid var(--success);
            padding: 10px 14px;
            font-size: 12px;
            border-radius: 0 4px 4px 0;
            color: #d1fae5;
        }}
        .empty-state {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 48px;
            text-align: center;
        }}
        .footer {{
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 12px;
            color: var(--muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>RepoMedic Security Audit</h1>
                <p style="color: var(--muted); margin: 4px 0 0 0; font-size: 14px;">Target: <code>{target_esc}</code></p>
            </div>
            <div>
                {status_badge}
            </div>
        </div>

        <div class="stats-grid">
            <div class="card">
                <div class="card-label">Security Grade</div>
                <div class="card-value" style="color: {grade_color};">{grade} <span style="font-size: 18px; color: var(--muted);">({score_val}/100)</span></div>
            </div>
            <div class="card">
                <div class="card-label">Findings Detected</div>
                <div class="card-value">{len(findings)}</div>
            </div>
            <div class="card">
                <div class="card-label">Files Inspected</div>
                <div class="card-value">{report.evidence.files_scanned}</div>
            </div>
            <div class="card">
                <div class="card-label">Scan Duration</div>
                <div class="card-value">{duration_s}</div>
            </div>
        </div>

        <h2>Executive Summary & AI Triage ({ai_mode_badge} Model: <code>{ai_model}</code>)</h2>
        <div class="card">
            <p style="margin: 0; font-size: 14px; line-height: 1.6;">{summary_html}</p>
        </div>

        <h2>Scanner Subsystem Health</h2>
        <div class="card" style="padding: 0; overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Scanner</th>
                        <th>Status</th>
                        <th>Required</th>
                        <th>Duration</th>
                        <th>Findings</th>
                        <th>Diagnostics</th>
                    </tr>
                </thead>
                <tbody>
                    {health_table_body}
                </tbody>
            </table>
        </div>

        <h2>Detected Security Findings ({len(findings)})</h2>
        {findings_html}

        <div class="footer">
            RepoMedic Static Analysis Engine &bull; Security boundary: Static analysis only. Target code is never executed.
        </div>
    </div>
</body>
</html>
"""
