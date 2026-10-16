"use client";

import React, { useEffect, useState, use, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FolderGit2,
  Clock,
  ArrowRight,
  ShieldCheck,
  Ban,
  FileCode,
  Layers,
  Sparkles,
  RefreshCw,
  Lock,
} from "lucide-react";
import { ScanJob, JobState } from "@/types/repomedic";
import { cancelJob, getJobStatus } from "@/lib/api";
import { StatusBadge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { formatDurationMs, formatRelativeTimestamp } from "@/lib/formatters";

function LiveAuditContent({ id }: { id: string }) {
  const router = useRouter();
  const [job, setJob] = useState<ScanJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    let timer: NodeJS.Timeout;
    const pollInterval = 1500;

    async function poll() {
      try {
        const currentJob = await getJobStatus(id);
        if (!mountedRef.current) return;

        setJob(currentJob);
        setLoading(false);
        setError(null);
        setLastUpdated(new Date());

        // Stop polling on terminal states
        if (["completed", "partial", "failed"].includes(currentJob.state)) {
          // If completed or partial with report, provide smooth transition after 1.5s
          if (["completed", "partial"].includes(currentJob.state)) {
            setTimeout(() => {
              if (mountedRef.current) {
                router.push(`/audits/${id}/results`);
              }
            }, 1800);
          }
          return;
        }

        // Continue polling
        timer = setTimeout(poll, pollInterval);
      } catch (err: unknown) {
        if (!mountedRef.current) return;
        const msg = err instanceof Error ? err.message : "Failed to poll job status from backend.";
        setError(msg);
        setLoading(false);
        // Back off on error
        timer = setTimeout(poll, 4000);
      }
    }

    poll();

    return () => {
      mountedRef.current = false;
      clearTimeout(timer);
    };
  }, [id, router]);

  async function handleCancel() {
    if (!job || (job.state !== "queued" && job.state !== "running")) return;
    try {
      setCancelling(true);
      const updated = await cancelJob(job.job_id);
      setJob(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert(`Cancellation failed: ${msg}`);
    } finally {
      setCancelling(false);
    }
  }

  // Derive stage status from real current_step & state
  const isTerminal = job ? ["completed", "partial", "failed"].includes(job.state) : false;
  const isCancelled = job?.current_step === "cancelled_by_user" || (job?.state === "failed" && job?.error?.includes("cancelled"));

  const stages = [
    {
      id: "prep",
      label: "Repository Preparation & Ingestion",
      desc: "Target clone, directory size bounds, candidate file discovery",
      icon: FolderGit2,
      isDone: job ? job.progress_percent >= 25 || isTerminal : false,
      isActive: job?.current_step?.includes("cloning") || (job?.state === "running" && (job?.progress_percent ?? 0) < 30),
    },
    {
      id: "custom",
      label: "Custom Security & Secret Rules",
      desc: "Regex patterns for API tokens, hardcoded credentials, and private keys",
      icon: Lock,
      isDone: job ? job.progress_percent >= 50 || isTerminal : false,
      isActive: job?.state === "running" && (job?.progress_percent ?? 0) >= 30 && (job?.progress_percent ?? 0) < 60,
    },
    {
      id: "ast",
      label: "Python AST Syntax & Safety",
      desc: "Abstract syntax tree evaluation for code execution and eval/exec sinks",
      icon: FileCode,
      isDone: job ? job.progress_percent >= 60 || isTerminal : false,
      isActive: job?.state === "running" && (job?.progress_percent ?? 0) >= 50 && (job?.progress_percent ?? 0) < 70,
    },
    {
      id: "osv",
      label: "OSV Open Source Vulnerability DB",
      desc: "Dependency lockfile cross-referencing against global CVE/GHSA advisories",
      icon: Layers,
      isDone: job ? job.progress_percent >= 75 || isTerminal : false,
      isActive: job?.state === "running" && (job?.progress_percent ?? 0) >= 60 && (job?.progress_percent ?? 0) < 80,
    },
    {
      id: "semgrep",
      label: "Semgrep Ruleset Execution",
      desc: "Configured static taint analysis and vulnerability pattern matching",
      icon: ShieldCheck,
      isDone: job ? job.progress_percent >= 85 || isTerminal : false,
      isActive: job?.state === "running" && (job?.progress_percent ?? 0) >= 70 && (job?.progress_percent ?? 0) < 90,
    },
    {
      id: "ai",
      label: "AI Triage & Citation Verification",
      desc: "Groq LLM triage diagnosis, remediation priority, and citation validation",
      icon: Sparkles,
      isDone: isTerminal,
      isActive: job?.state === "running" && (job?.progress_percent ?? 0) >= 85,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: "Overview", href: "/" },
          { label: `Audit #${id.slice(0, 8)}` },
        ]}
        title={job?.target ? job.target.replace("https://github.com/", "") : `Audit #${id.slice(0, 8)}`}
        description={`Job ID: ${id}`}
        actions={job && <StatusBadge status={job.state} />}
      />

      {/* Main Balanced 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Column (2/3): Status & Timeline */}
        <div className="lg:col-span-2 space-y-5">
          {/* Status Box */}
          <div className="p-5 sm:p-6 rounded-lg border border-[#30363D] bg-[#161B22] space-y-4 shadow-xs">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#8B949E]">
                  Current Status
                </span>
                <h2 className="text-lg font-bold text-[#E6EDF3] mt-0.5">
                  {job?.state === "queued" && "Scan Enqueued in Worker Pool"}
                  {job?.state === "running" && "Analyzing Repository Security"}
                  {job?.state === "completed" && "Audit Completed Successfully"}
                  {job?.state === "partial" && "Partial Audit Completed (Incomplete Coverage)"}
                  {job?.state === "failed" && (isCancelled ? "Audit Cancelled by User" : "Audit Execution Failed")}
                </h2>
              </div>
              <div className="text-right">
                <span className="font-mono text-sm font-bold text-[#58A6FF]">
                  {job?.progress_percent ?? 0}%
                </span>
              </div>
            </div>

            {/* Real Progress Bar */}
            <div className="w-full bg-[#0D1117] h-2 rounded-full overflow-hidden border border-[#21262D] relative">
              {job?.state === "running" && (job?.progress_percent === 0 || !job?.progress_percent) ? (
                <div className="h-full bg-[#58A6FF] w-1/3 rounded-full animate-indeterminate" />
              ) : (
                <div
                  className={`h-full transition-all duration-300 rounded-full ${
                    job?.state === "completed"
                      ? "bg-[#3FB950]"
                      : job?.state === "partial"
                      ? "bg-[#D29922]"
                      : job?.state === "failed"
                      ? "bg-[#F85149]"
                      : "bg-[#58A6FF]"
                  }`}
                  style={{ width: `${Math.max(job?.progress_percent ?? 0, 5)}%` }}
                />
              )}
            </div>

            {/* Step Message */}
            <div className="text-xs text-[#8B949E] font-mono flex items-center justify-between">
              <span>Stage: {job?.current_step || "initializing"}</span>
              {job?.report?.evidence?.findings && (
                <span className="text-[#E6EDF3]">
                  {job.report.evidence.findings.length} findings emitted
                </span>
              )}
            </div>

            {/* Terminal Actions */}
            {job && ["completed", "partial"].includes(job.state) && (
              <div className="pt-2 border-t border-[#21262D] flex items-center justify-between">
                <span className="text-xs text-[#3FB950] flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Report ready. Redirecting automatically...</span>
                </span>
                <Link
                  href={`/audits/${id}/results`}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold bg-[#58A6FF] hover:bg-[#79C0FF] text-[#0D1117] transition-colors"
                >
                  <span>View Results</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}

            {job?.state === "failed" && (
              <div className="pt-2 border-t border-[#21262D] text-xs text-[#F85149] space-y-1">
                <span className="font-semibold block">Failure Notice:</span>
                <p className="font-mono text-[11px] bg-[#0D1117] p-2 rounded border border-[#21262D]">
                  {job.error || "Execution terminated unexpectedly."}
                </p>
                <div className="pt-2">
                  <Link
                    href="/audits/new"
                    className="inline-flex items-center gap-1 px-3 py-1 rounded bg-[#21262D] hover:bg-[#30363D] text-[#E6EDF3] font-medium"
                  >
                    <span>Start New Audit</span>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Scanner Pipeline Timeline (Section 7.3) */}
          <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] space-y-4 shadow-xs">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8B949E]">
              Engine Pipeline Timeline
            </h3>

            <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#21262D]">
              {stages.map((stg) => {
                const Icon = stg.icon;
                return (
                  <div key={stg.id} className="relative flex items-start gap-3 text-xs">
                    {/* Status indicator dot */}
                    <div
                      className={`absolute -left-6 mt-0.5 w-5 h-5 rounded-full border flex items-center justify-center transition-colors ${
                        stg.isDone
                          ? "bg-[#3FB950]/20 border-[#3FB950] text-[#3FB950]"
                          : stg.isActive
                          ? "bg-[#58A6FF]/20 border-[#58A6FF] text-[#58A6FF] animate-pulse"
                          : "bg-[#0D1117] border-[#30363D] text-[#6E7681]"
                      }`}
                    >
                      {stg.isDone ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : stg.isActive ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <span className="w-1.5 h-1.5 rounded-full bg-[#30363D]" />
                      )}
                    </div>

                    <div className="space-y-0.5 flex-1">
                      <div className="flex items-center justify-between">
                        <span
                          className={`font-semibold ${
                            stg.isDone
                              ? "text-[#E6EDF3]"
                              : stg.isActive
                              ? "text-[#58A6FF]"
                              : "text-[#8B949E]"
                          }`}
                        >
                          {stg.label}
                        </span>
                        <span className="text-[10px] font-mono text-[#8B949E]">
                          {stg.isDone ? "Completed" : stg.isActive ? "Running..." : "Pending"}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#8B949E] leading-relaxed">
                        {stg.desc}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Sidebar Column (1/3): Job Metadata & Actions */}
        <div className="space-y-5">
          {/* Job Configuration Card */}
          <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] space-y-4 shadow-xs">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8B949E]">
              Job Metadata
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[10px] text-[#8B949E] uppercase font-mono block">Target Repository</span>
                <span className="text-[#58A6FF] font-mono break-all block mt-0.5">
                  {job?.target || "Loading target..."}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-[#8B949E] uppercase font-mono block">Job UUID</span>
                <span className="text-[#E6EDF3] font-mono text-[11px] block mt-0.5">{id}</span>
              </div>

              <div>
                <span className="text-[10px] text-[#8B949E] uppercase font-mono block">Enqueued At</span>
                <span className="text-[#8B949E] font-mono text-[11px] block mt-0.5">
                  {job?.created_at ? new Date(job.created_at).toLocaleString() : "Just now"}
                </span>
              </div>

              {lastUpdated && (
                <div className="pt-2 border-t border-[#21262D] text-[11px] text-[#8B949E] flex items-center justify-between">
                  <span>Last Polled:</span>
                  <span className="font-mono text-[#E6EDF3]">
                    {lastUpdated.toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>

            {/* Cancel Action */}
            {job && (job.state === "queued" || job.state === "running") && (
              <div className="pt-3 border-t border-[#21262D]">
                <button
                  onClick={handleCancel}
                  disabled={cancelling}
                  className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-semibold bg-[#21262D] hover:bg-[#F85149]/20 hover:text-[#F85149] text-[#8B949E] border border-[#30363D] hover:border-[#F85149]/40 transition-colors disabled:opacity-50"
                >
                  <Ban className="w-3.5 h-3.5" />
                  <span>{cancelling ? "Cancelling..." : "Cancel Scan"}</span>
                </button>
              </div>
            )}
          </div>

          {/* Security Guarantee Notice */}
          <div className="p-4 rounded-lg bg-[#0D1117] border border-[#21262D] space-y-1.5 text-xs text-[#8B949E]">
            <div className="flex items-center gap-1.5 text-[#E6EDF3] font-semibold text-[11px]">
              <Lock className="w-3 h-3 text-[#58A6FF]" />
              <span>Zero Execution Guarantee</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Target source code is cloned into ephemeral memory and analyzed strictly as text and AST trees. No code is installed, imported, or run.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LiveAuditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <LiveAuditContent id={id} />;
}
