"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  FolderGit2,
  Clock,
  FileCheck,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  ArrowLeft,
  CheckCircle2,
  ShieldAlert,
} from "lucide-react";
import { ScanReport } from "@/types/repomedic";
import { getJobReport } from "@/lib/api";
import { PartialAuditWarning } from "@/components/audit/PartialAuditWarning";
import { ScannerHealthTable } from "@/components/audit/ScannerHealthTable";
import { ExportButtons } from "@/components/audit/ExportButtons";
import { FindingsList } from "@/components/findings/FindingsList";
import { RiskScoreRing } from "@/components/audit/RiskScoreRing";
import { StatusBadge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { formatDurationMs } from "@/lib/formatters";

function AuditResultsContent({ id }: { id: string }) {
  const [report, setReport] = useState<ScanReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getJobReport(id);
        setReport(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to retrieve scan report from backend.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3">
        <RefreshCw className="w-6 h-6 animate-spin text-[#58A6FF] mx-auto" />
        <p className="text-xs text-[#8B949E]">Loading completed audit report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="py-12 max-w-xl mx-auto space-y-4">
        <div className="p-6 rounded-lg border border-[#F85149]/40 bg-[#F85149]/10 text-center space-y-3">
          <AlertTriangle className="w-8 h-8 text-[#F85149] mx-auto" />
          <h2 className="text-base font-bold text-[#E6EDF3]">Report Unavailable</h2>
          <p className="text-xs text-[#8B949E] leading-relaxed">
            {error || "The audit report could not be found or has not concluded."}
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link
              href={`/audits/${id}`}
              className="px-3 py-1.5 rounded-md bg-[#21262D] hover:bg-[#30363D] text-xs text-[#E6EDF3] font-medium"
            >
              Back to Polling
            </Link>
            <Link
              href="/"
              className="px-3 py-1.5 rounded-md bg-[#58A6FF] hover:bg-[#79C0FF] text-xs text-[#0D1117] font-semibold"
            >
              Return to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const findings = report.evidence?.findings || [];
  const isPartial = report.scan_health?.partial_audit;

  return (
    <div className="space-y-6">
      {/* Page Header (Section 9.1) */}
      <PageHeader
        breadcrumbs={[
          { label: "Overview", href: "/" },
          { label: "Audits", href: "/#recent-audits" },
          { label: `#${id.slice(0, 8)} Results` },
        ]}
        title={report.target.replace("https://github.com/", "")}
        description={`Audit target: ${report.target}`}
        actions={
          <div className="flex items-center gap-3">
            <StatusBadge status={report.scan_health.audit_status} />
            <ExportButtons jobId={id} />
          </div>
        }
      />

      {/* Prominent Incomplete Audit Banner (Section 9.2) */}
      <PartialAuditWarning scanHealth={report.scan_health} />

      {/* Signature Risk Score & Operational Summary (Section 08 / 9.3) */}
      <div className="space-y-4">
        <RiskScoreRing
          score={report.score}
          partialAudit={isPartial}
          auditStatus={report.scan_health.audit_status}
        />

        {/* Secondary Metric Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* Total Findings */}
          <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
            <span className="text-[10px] text-[#8B949E] uppercase font-mono font-medium block">
              Total Findings
            </span>
            <div className="text-2xl font-bold font-mono text-[#E6EDF3] mt-1">
              {findings.length}
            </div>
            <div className="flex items-center gap-1.5 mt-1 text-[11px] font-mono">
              <span className="text-[#F85149] font-semibold">
                {report.score.severity_counts["critical"] || 0} crit
              </span>
              <span className="text-[#30363D]">&bull;</span>
              <span className="text-[#F0883E] font-semibold">
                {report.score.severity_counts["high"] || 0} high
              </span>
            </div>
          </div>

          {/* Files Inspected */}
          <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
            <span className="text-[10px] text-[#8B949E] uppercase font-mono font-medium block">
              Files Inspected
            </span>
            <div className="text-2xl font-bold font-mono text-[#E6EDF3] mt-1">
              {report.evidence.files_scanned}
            </div>
            <span className="text-[11px] text-[#8B949E] mt-1 block truncate">
              {report.evidence.large_files_skipped} skipped for size
            </span>
          </div>

          {/* Total Scan Time */}
          <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
            <span className="text-[10px] text-[#8B949E] uppercase font-mono font-medium block">
              Execution Duration
            </span>
            <div className="text-2xl font-bold font-mono text-[#58A6FF] mt-1">
              {formatDurationMs(report.scan_health.total_duration_ms)}
            </div>
            <span className="text-[11px] text-[#8B949E] mt-1 block font-mono">
              {report.scan_health.finish_time
                ? new Date(report.scan_health.finish_time).toLocaleTimeString()
                : "Completed"}
            </span>
          </div>

          {/* AI Inference Mode */}
          <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
            <span className="text-[10px] text-[#8B949E] uppercase font-mono font-medium block">
              Triage Mode
            </span>
            <div className="text-lg font-bold text-[#E6EDF3] mt-1 capitalize truncate">
              {report.ai_triage.mode === "groq" ? "Groq LLM" : "Deterministic"}
            </div>
            <span className="text-[11px] text-[#8B949E] mt-1 block font-mono truncate" title={report.ai_triage.model}>
              {report.ai_triage.model || "Offline"}
            </span>
          </div>
        </div>
      </div>

      {/* AI Triage Executive Summary */}
      {report.ai_triage?.executive_summary && (
        <div className="rounded-lg border border-[#30363D] bg-[#161B22] p-5 space-y-3 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#21262D] pb-3">
            <h2 className="text-xs font-semibold text-[#E6EDF3] uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-[#58A6FF]" />
              <span>AI Triage & Executive Assessment</span>
            </h2>
            <div className="flex items-center gap-2 text-[10px] font-mono text-[#8B949E]">
              <span>Citations: {report.ai_triage.citation_validity_percent}% verified</span>
              <span>&bull;</span>
              <span>Latency: {report.ai_triage.duration_ms}ms</span>
            </div>
          </div>
          <p className="text-xs text-[#E6EDF3] leading-relaxed bg-[#0D1117] p-3.5 rounded-md border border-[#21262D]">
            {report.ai_triage.executive_summary}
          </p>
        </div>
      )}

      {/* Scanner Subsystem Health Table */}
      <section className="space-y-3">
        <ScannerHealthTable scanners={report.scan_health.scanners} />
      </section>

      {/* Normalized Security Findings Workspace (Section 9.4 - 9.7) */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider">
            Normalized Findings Workspace ({findings.length})
          </h2>
          <span className="text-[11px] font-mono text-[#6E7681]">
            Deterministic findings cross-referenced with AST & CVE database
          </span>
        </div>
        <FindingsList
          findings={findings}
          diagnoses={report.ai_triage?.diagnoses || []}
        />
      </section>
    </div>
  );
}

export default function AuditResultsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <AuditResultsContent id={id} />;
}
