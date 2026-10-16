"use client";

import React, { useCallback, useEffect, useState, useTransition } from "react";
import Link from "next/link";
import {
  PlusCircle,
  RefreshCw,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  FolderGit2,
  Clock,
  Activity,
  Layers,
  FileCode,
  ExternalLink,
} from "lucide-react";
import { ScanJob, ReadinessResponse, BenchmarkSummary } from "@/types/repomedic";
import { listRecentJobs, checkBackendReadiness, getBenchmarkSummary } from "@/lib/api";
import { StatusBadge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { formatRelativeTimestamp, formatDurationMs } from "@/lib/formatters";

export default function DashboardPage() {
  const [jobs, setJobs] = useState<ScanJob[]>([]);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setError(null);

    try {
      const [jobsRes, readyRes, benchRes] = await Promise.allSettled([
        listRecentJobs(20),
        checkBackendReadiness(),
        getBenchmarkSummary(),
      ]);

      if (jobsRes.status === "fulfilled") {
        setJobs(jobsRes.value);
      } else {
        console.warn("Failed to retrieve jobs list:", jobsRes.reason);
      }

      if (readyRes.status === "fulfilled") {
        setReadiness(readyRes.value);
      }

      if (benchRes.status === "fulfilled") {
        setBenchmark(benchRes.value);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load dashboard data from backend.";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([
      listRecentJobs(20),
      checkBackendReadiness(),
      getBenchmarkSummary(),
    ]).then(([jobsRes, readyRes, benchRes]) => {
      if (cancelled) return;
      if (jobsRes.status === "fulfilled") {
        setJobs(jobsRes.value);
      } else {
        console.warn("Failed to retrieve jobs list:", jobsRes.reason);
      }

      if (readyRes.status === "fulfilled") {
        setReadiness(readyRes.value);
      }

      if (benchRes.status === "fulfilled") {
        setBenchmark(benchRes.value);
      }
      setLoading(false);
    }).catch((err: unknown) => {
      if (cancelled) return;
      const msg = err instanceof Error ? err.message : "Failed to load dashboard data from backend.";
      setError(msg);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  // Compute operational summary metrics strictly from real backend responses
  const totalAudits = jobs.length;
  const completedAudits = jobs.filter((j) => j.state === "completed" || j.state === "partial").length;
  const latestCompletedJob = jobs.find((j) => j.report && (j.state === "completed" || j.state === "partial"));
  const latestFindingsCount = latestCompletedJob?.report?.evidence?.findings?.length;

  const scannerList = readiness?.scanners ? Object.entries(readiness.scanners) : [];
  const readyScannerCount = scannerList.filter(([_, status]) => status.startsWith("available")).length;

  return (
    <div className="space-y-6">
      {/* Page Header (Section 5.1) */}
      <PageHeader
        eyebrow="WORKSPACE"
        title="Overview"
        description="Repository audit status, findings, and scanner health."
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadDashboard(true)}
              disabled={refreshing || loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-[#161B22] hover:bg-[#21262D] text-[#8B949E] hover:text-[#E6EDF3] border border-[#30363D] transition-colors disabled:opacity-50"
              title="Refresh dashboard state"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-[#58A6FF]" : ""}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
            <Link
              href="/audits/new"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold bg-[#58A6FF] hover:bg-[#79C0FF] text-[#0D1117] transition-colors shadow-xs"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>New audit</span>
            </Link>
          </div>
        }
      />

      {/* Operational Summary (Section 5.2: 3-4 compact metric modules) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Total Audits */}
        <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
          <div className="text-[11px] uppercase font-mono tracking-wider text-[#8B949E] font-medium">
            Total Audits
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight text-[#E6EDF3] mt-1">
            {loading ? <span className="text-[#6E7681] text-base font-sans">Loading...</span> : totalAudits}
          </div>
          <div className="text-[11px] text-[#8B949E] mt-1 flex items-center gap-1">
            <span>{completedAudits} completed / partial</span>
          </div>
        </div>

        {/* Audits Completed */}
        <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
          <div className="text-[11px] uppercase font-mono tracking-wider text-[#8B949E] font-medium">
            Completed Runs
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight text-[#3FB950] mt-1">
            {loading ? <span className="text-[#6E7681] text-base font-sans">Loading...</span> : completedAudits}
          </div>
          <div className="text-[11px] text-[#8B949E] mt-1">
            <span>{jobs.filter((j) => j.state === "running" || j.state === "queued").length} active in pool</span>
          </div>
        </div>

        {/* Latest Audit Findings */}
        <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
          <div className="text-[11px] uppercase font-mono tracking-wider text-[#8B949E] font-medium">
            Latest Findings
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight text-[#E6EDF3] mt-1">
            {loading ? (
              <span className="text-[#6E7681] text-base font-sans">Loading...</span>
            ) : latestFindingsCount !== undefined ? (
              latestFindingsCount
            ) : (
              <span className="text-base text-[#6E7681] font-sans">None yet</span>
            )}
          </div>
          <div className="text-[11px] text-[#8B949E] mt-1 truncate">
            {latestCompletedJob ? (
              <span title={latestCompletedJob.target}>{latestCompletedJob.target.replace("https://github.com/", "")}</span>
            ) : (
              <span>Awaiting first completed scan</span>
            )}
          </div>
        </div>

        {/* Scanner Engine Readiness */}
        <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
          <div className="text-[11px] uppercase font-mono tracking-wider text-[#8B949E] font-medium">
            Engine Readiness
          </div>
          <div className="text-2xl font-bold font-mono tracking-tight text-[#58A6FF] mt-1">
            {loading ? (
              <span className="text-[#6E7681] text-base font-sans">Loading...</span>
            ) : readiness ? (
              `${readyScannerCount}/${scannerList.length}`
            ) : (
              <span className="text-base text-[#D29922] font-sans">Offline</span>
            )}
          </div>
          <div className="text-[11px] text-[#8B949E] mt-1 flex items-center gap-1.5">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                readiness?.status === "ready" ? "bg-[#3FB950]" : "bg-[#D29922]"
              }`}
            />
            <span>
              {readiness?.ai_inference?.mode === "groq"
                ? "Deterministic + AI Triage"
                : "Deterministic Core Only"}
            </span>
          </div>
        </div>
      </div>

      {/* Main Section: Recent Audits Table (Section 5.3) */}
      <section id="recent-audits" className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#8B949E]">
            Recent Audits ({jobs.length})
          </h2>
          {jobs.length > 0 && (
            <span className="text-[11px] text-[#6E7681] font-mono">
              Live updates via asynchronous queue
            </span>
          )}
        </div>

        {loading ? (
          <div className="p-8 rounded-lg border border-[#30363D] bg-[#161B22] text-center space-y-2">
            <RefreshCw className="w-5 h-5 animate-spin text-[#58A6FF] mx-auto" />
            <span className="text-xs text-[#8B949E]">Loading recent audits...</span>
          </div>
        ) : jobs.length === 0 ? (
          /* Dashboard Empty State (Section 5.5) */
          <div className="rounded-lg border border-[#30363D] bg-[#161B22] p-12 text-center space-y-3 shadow-xs">
            <div className="w-10 h-10 rounded-full bg-[#21262D] border border-[#30363D] flex items-center justify-center text-[#8B949E] mx-auto">
              <FolderGit2 className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-[#E6EDF3]">No audits yet</h3>
              <p className="text-xs text-[#8B949E] max-w-sm mx-auto leading-relaxed">
                Start your first repository security audit by providing a public GitHub URL. The backend will inspect candidate files with zero code execution.
              </p>
            </div>
            <div className="pt-2">
              <Link
                href="/audits/new"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-semibold bg-[#58A6FF] hover:bg-[#79C0FF] text-[#0D1117] transition-colors"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Start your first audit</span>
              </Link>
            </div>
          </div>
        ) : (
          /* Real Audits Table */
          <div className="border border-[#30363D] rounded-lg bg-[#161B22] overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-[#21262D] text-left text-xs">
                <thead className="bg-[#0D1117] text-[#8B949E] text-[11px] font-semibold uppercase tracking-wider">
                  <tr>
                    <th scope="col" className="px-4 py-2.5">Repository</th>
                    <th scope="col" className="px-4 py-2.5">Audit ID</th>
                    <th scope="col" className="px-4 py-2.5">Status</th>
                    <th scope="col" className="px-4 py-2.5">Score / Findings</th>
                    <th scope="col" className="px-4 py-2.5">Created</th>
                    <th scope="col" className="px-4 py-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#21262D]">
                  {jobs.map((job) => {
                    const isCompleted = job.state === "completed" || job.state === "partial";
                    const findingsCount = job.report?.evidence?.findings?.length;
                    const score = job.report?.score?.score;
                    const grade = job.report?.score?.grade;

                    return (
                      <tr
                        key={job.job_id}
                        className="hover:bg-[#21262D]/60 transition-colors group"
                      >
                        <td className="px-4 py-3 align-middle font-medium text-[#E6EDF3]">
                          <div className="flex items-center space-x-2">
                            <FolderGit2 className="w-4 h-4 text-[#8B949E] shrink-0" />
                            <span className="font-semibold text-xs truncate max-w-xs sm:max-w-md block" title={job.target}>
                              {job.target.replace("https://github.com/", "")}
                            </span>
                          </div>
                        </td>

                        <td className="px-4 py-3 align-middle font-mono text-[11px] text-[#8B949E]">
                          #{job.job_id.slice(0, 8)}
                        </td>

                        <td className="px-4 py-3 align-middle">
                          <StatusBadge status={job.state} />
                        </td>

                        <td className="px-4 py-3 align-middle text-xs font-mono">
                          {isCompleted ? (
                            <div className="flex items-center gap-2">
                              {score !== undefined && (
                                <span className="font-semibold text-[#E6EDF3]">
                                  {score}/100 <span className="text-[10px] text-[#8B949E]">({grade})</span>
                                </span>
                              )}
                              <span className="text-[#8B949E]">&bull;</span>
                              <span className="text-[#8B949E]">
                                {findingsCount !== undefined ? `${findingsCount} findings` : "Report ready"}
                              </span>
                            </div>
                          ) : (
                            <span className="text-[#8B949E] italic font-sans text-[11px]">
                              {job.current_step || "In queue..."}
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-3 align-middle text-xs font-mono text-[#8B949E] whitespace-nowrap">
                          {formatRelativeTimestamp(job.created_at)}
                        </td>

                        <td className="px-4 py-3 align-middle text-right whitespace-nowrap">
                          <Link
                            href={isCompleted ? `/audits/${job.job_id}/results` : `/audits/${job.job_id}`}
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#58A6FF] hover:underline"
                          >
                            <span>{isCompleted ? "View Report" : "Track Progress"}</span>
                            <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* Scanner Health Summary (Section 5.4) */}
      <section className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#8B949E]">
            Scanner Engine Health & Readiness
          </h2>
          <Link
            href="/diagnostics"
            className="text-[11px] text-[#58A6FF] hover:underline flex items-center gap-1 font-medium"
          >
            <span>Detailed Diagnostics</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {scannerList.map(([key, stat]) => {
            const isAvail = stat.startsWith("available");
            const engineNames: Record<string, string> = {
              custom_rules: "Custom Security Rules",
              python_ast: "Python AST Analyzer",
              osv: "OSV Vulnerability DB",
              semgrep: "Semgrep Ruleset",
            };

            return (
              <div
                key={key}
                className="p-3.5 rounded-lg bg-[#161B22] border border-[#30363D] space-y-1.5 shadow-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-[#E6EDF3]">
                    {engineNames[key] || key}
                  </span>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      isAvail ? "bg-[#3FB950]" : "bg-[#D29922]"
                    }`}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-mono text-[#8B949E]">{key}</span>
                  <span
                    className={`font-medium ${
                      isAvail ? "text-[#3FB950]" : "text-[#D29922]"
                    }`}
                  >
                    {stat}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
