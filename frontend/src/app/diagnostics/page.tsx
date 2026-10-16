"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Cpu,
  ShieldCheck,
  Sparkles,
  Server,
  Lock,
  Layers,
  Settings,
} from "lucide-react";
import { DiagnosticsResponse, ReadinessResponse } from "@/types/repomedic";
import { checkBackendHealth, checkBackendReadiness, getDiagnostics } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatusBadge } from "@/components/ui/Badge";

export default function DiagnosticsPage() {
  const [diagnostics, setDiagnostics] = useState<DiagnosticsResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [liveness, setLiveness] = useState<{ status: string; version: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setError(null);

    try {
      const [liveRes, readyRes, diagRes] = await Promise.allSettled([
        checkBackendHealth(),
        checkBackendReadiness(),
        getDiagnostics(),
      ]);

      if (liveRes.status === "fulfilled") setLiveness(liveRes.value);
      if (readyRes.status === "fulfilled") setReadiness(readyRes.value);
      if (diagRes.status === "fulfilled") setDiagnostics(diagRes.value);

      if (liveRes.status === "rejected" && readyRes.status === "rejected" && diagRes.status === "rejected") {
        throw new Error("Unable to contact backend diagnostic endpoints. Ensure the backend server is running.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Diagnostic probe failed.";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([
      checkBackendHealth(),
      checkBackendReadiness(),
      getDiagnostics(),
    ]).then(([liveRes, readyRes, diagRes]) => {
      if (cancelled) return;
      if (liveRes.status === "fulfilled") setLiveness(liveRes.value);
      if (readyRes.status === "fulfilled") setReadiness(readyRes.value);
      if (diagRes.status === "fulfilled") setDiagnostics(diagRes.value);

      if (liveRes.status === "rejected" && readyRes.status === "rejected" && diagRes.status === "rejected") {
        setError("Unable to contact backend diagnostic endpoints. Ensure the backend server is running.");
      }
      setLoading(false);
    }).catch((err: unknown) => {
      if (cancelled) return;
      const msg = err instanceof Error ? err.message : "Diagnostic probe failed.";
      setError(msg);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header (Section 12) */}
      <PageHeader
        breadcrumbs={[
          { label: "Overview", href: "/" },
          { label: "Scanner Health & Diagnostics" },
        ]}
        title="Scanner Health & System Diagnostics"
        description="Verify engine availability, host CLI tool dependencies, AI discovery parameters, and execution limits."
        actions={
          <button
            onClick={() => loadData(true)}
            disabled={refreshing || loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-[#161B22] hover:bg-[#21262D] text-[#8B949E] hover:text-[#E6EDF3] border border-[#30363D] transition-colors disabled:opacity-50"
            title="Refresh diagnostics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-[#58A6FF]" : ""}`} />
            <span>Re-probe Engine</span>
          </button>
        }
      />

      {loading ? (
        <div className="py-20 text-center space-y-3">
          <RefreshCw className="w-6 h-6 animate-spin text-[#58A6FF] mx-auto" />
          <p className="text-xs text-[#8B949E]">Querying subsystem diagnostic probes...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-lg border border-[#F85149]/40 bg-[#F85149]/10 text-center space-y-3 max-w-xl mx-auto">
          <AlertTriangle className="w-8 h-8 text-[#F85149] mx-auto" />
          <h3 className="text-sm font-semibold text-[#E6EDF3]">Diagnostics Probes Unreachable</h3>
          <p className="text-xs text-[#8B949E]">{error}</p>
          <button
            onClick={() => loadData()}
            className="mt-2 px-3 py-1.5 rounded-md bg-[#21262D] hover:bg-[#30363D] text-xs font-medium text-[#E6EDF3]"
          >
            Retry Probe
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Service Liveness vs Readiness (Section 12) */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] space-y-1 shadow-xs">
              <span className="text-[10px] uppercase font-mono text-[#8B949E] block">
                Service Liveness
              </span>
              <div className="flex items-center gap-2 mt-1">
                <span className="w-2.5 h-2.5 rounded-full bg-[#3FB950]" />
                <span className="text-base font-bold text-[#E6EDF3] capitalize">
                  {liveness?.status || "Online"}
                </span>
              </div>
              <span className="text-[11px] text-[#8B949E] block">
                FastAPI HTTP Server responding
              </span>
            </div>

            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] space-y-1 shadow-xs">
              <span className="text-[10px] uppercase font-mono text-[#8B949E] block">
                Audit Readiness
              </span>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    readiness?.status === "ready" ? "bg-[#3FB950]" : "bg-[#D29922]"
                  }`}
                />
                <span className="text-base font-bold text-[#E6EDF3] capitalize">
                  {readiness?.status || "Ready"}
                </span>
              </div>
              <span className="text-[11px] text-[#8B949E] block">
                {readiness?.status === "ready" ? "Ready to accept scan jobs" : "Subsystem degraded"}
              </span>
            </div>

            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] space-y-1 shadow-xs">
              <span className="text-[10px] uppercase font-mono text-[#8B949E] block">
                Runtime Environment
              </span>
              <div className="text-base font-bold text-[#58A6FF] font-mono mt-1 capitalize">
                {diagnostics?.environment || "development"}
              </div>
              <span className="text-[11px] text-[#8B949E] block">
                Core Version v{diagnostics?.version || "2.0.0"}
              </span>
            </div>
          </div>

          {/* Scanner Policies & Subsystems */}
          <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-[#21262D] pb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#E6EDF3] flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#58A6FF]" />
                <span>Scanner Engine Subsystems & Policies</span>
              </h3>
              <span className="text-[11px] font-mono text-[#8B949E]">
                Policy governs complete vs partial audit classification
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {/* Custom Rules */}
              <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#E6EDF3]">Custom Regex & Secret Rules</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#3FB950]/15 text-[#3FB950] border border-[#3FB950]/30">
                    {readiness?.scanners?.custom_rules || "available"}
                  </span>
                </div>
                <div className="text-[11px] text-[#8B949E] flex items-center justify-between">
                  <span>Mandatory Policy:</span>
                  <span className="text-[#E6EDF3] font-semibold">
                    {diagnostics?.scanner_policies?.custom_rules_required !== false ? "Required" : "Optional"}
                  </span>
                </div>
              </div>

              {/* Python AST */}
              <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#E6EDF3]">Python AST Parser</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#3FB950]/15 text-[#3FB950] border border-[#3FB950]/30">
                    {readiness?.scanners?.python_ast || "available"}
                  </span>
                </div>
                <div className="text-[11px] text-[#8B949E] flex items-center justify-between">
                  <span>Mandatory Policy:</span>
                  <span className="text-[#E6EDF3] font-semibold">
                    {diagnostics?.scanner_policies?.python_ast_required !== false ? "Required" : "Optional"}
                  </span>
                </div>
              </div>

              {/* OSV Dependency DB */}
              <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#E6EDF3]">OSV Open Source Vulnerabilities</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#3FB950]/15 text-[#3FB950] border border-[#3FB950]/30">
                    {readiness?.scanners?.osv || "available"}
                  </span>
                </div>
                <div className="text-[11px] text-[#8B949E] flex items-center justify-between">
                  <span>Mandatory Policy:</span>
                  <span className="text-[#E6EDF3] font-semibold">
                    {diagnostics?.scanner_policies?.osv_required !== false ? "Required" : "Optional"}
                  </span>
                </div>
              </div>

              {/* Semgrep */}
              <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#E6EDF3]">Semgrep Ruleset Engine</span>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                      readiness?.scanners?.semgrep?.startsWith("available")
                        ? "bg-[#3FB950]/15 text-[#3FB950] border-[#3FB950]/30"
                        : "bg-[#21262D] text-[#8B949E] border-[#30363D]"
                    }`}
                  >
                    {readiness?.scanners?.semgrep || "unavailable (optional)"}
                  </span>
                </div>
                <div className="text-[11px] text-[#8B949E] flex items-center justify-between">
                  <span>Mandatory Policy:</span>
                  <span className="text-[#8B949E]">
                    {diagnostics?.scanner_policies?.semgrep_required ? "Required" : "Optional (Graceful Fallback)"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* AI Discovery & Host Tooling */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Host Tools */}
            <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] space-y-3 shadow-xs">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#E6EDF3] flex items-center gap-2">
                <Cpu className="w-4 h-4 text-[#58A6FF]" />
                <span>Host Binary CLI Tooling</span>
              </h3>

              <div className="space-y-2 text-xs">
                <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D] flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="font-semibold text-[#E6EDF3] block">Git CLI (`git`)</span>
                    <span className="text-[11px] text-[#8B949E]">Required for shallow repository cloning</span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#3FB950]/10 text-[#3FB950] border border-[#3FB950]/30 font-semibold">
                    {diagnostics?.tools?.git_installed !== false ? "Installed" : "Missing"}
                  </span>
                </div>

                <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D] flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="font-semibold text-[#E6EDF3] block">Semgrep CLI (`semgrep`)</span>
                    <span className="text-[11px] text-[#8B949E]">Local static analysis engine binary</span>
                  </div>
                  <span
                    className={`text-[11px] font-mono px-2 py-0.5 rounded border font-semibold ${
                      diagnostics?.tools?.semgrep_installed
                        ? "bg-[#3FB950]/10 text-[#3FB950] border-[#3FB950]/30"
                        : "bg-[#21262D] text-[#8B949E] border-[#30363D]"
                    }`}
                  >
                    {diagnostics?.tools?.semgrep_installed ? "Installed" : "Not in PATH"}
                  </span>
                </div>
              </div>
            </div>

            {/* AI Model Discovery (Safe info without secrets) */}
            <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] space-y-3 shadow-xs">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#E6EDF3] flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#58A6FF]" />
                  <span>AI Model Discovery Telemetry</span>
                </h3>
                <span className="text-[10px] font-mono text-[#3FB950]">Zero-Secret Safe</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-[#8B949E]">Active Groq Model:</span>
                    <span className="font-mono text-xs font-semibold text-[#58A6FF]">
                      {diagnostics?.ai_discovery?.active_model || "llama-3.3-70b-versatile"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-[#8B949E]">Configured Override:</span>
                    <span className="font-mono text-[#E6EDF3]">
                      {diagnostics?.ai_discovery?.configured_override || "None (Dynamic Discovery)"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-[#8B949E]">Cached Model Count:</span>
                    <span className="font-mono text-[#E6EDF3]">
                      {diagnostics?.ai_discovery?.cached_model_count ?? 0} models cached
                    </span>
                  </div>
                </div>

                {diagnostics?.ai_discovery?.preferences && (
                  <div className="p-2.5 rounded-md bg-[#0D1117] border border-[#21262D] text-[11px]">
                    <span className="text-[#8B949E] block mb-1 font-semibold">Priority Preferences:</span>
                    <div className="flex flex-wrap gap-1 font-mono text-[10px]">
                      {diagnostics.ai_discovery.preferences.map((pref, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-[#21262D] text-[#8B949E]">
                          {pref}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Execution & Resource Bounds (Section 12) */}
          {diagnostics?.limits && (
            <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] space-y-3 shadow-xs">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#E6EDF3] flex items-center gap-2">
                <Settings className="w-4 h-4 text-[#58A6FF]" />
                <span>Operational Concurrency & Resource Bounds</span>
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
                <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D]">
                  <span className="text-[10px] text-[#8B949E] uppercase font-sans block">Max Parallel Scans</span>
                  <span className="text-base font-bold text-[#E6EDF3] mt-0.5 block">
                    {diagnostics.limits.max_concurrent_scans}
                  </span>
                </div>
                <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D]">
                  <span className="text-[10px] text-[#8B949E] uppercase font-sans block">Queue Capacity</span>
                  <span className="text-base font-bold text-[#E6EDF3] mt-0.5 block">
                    {diagnostics.limits.max_queue_capacity}
                  </span>
                </div>
                <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D]">
                  <span className="text-[10px] text-[#8B949E] uppercase font-sans block">Scan Timeout</span>
                  <span className="text-base font-bold text-[#E6EDF3] mt-0.5 block">
                    {diagnostics.limits.scan_timeout_seconds}s
                  </span>
                </div>
                <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D]">
                  <span className="text-[10px] text-[#8B949E] uppercase font-sans block">Max Repo Size</span>
                  <span className="text-base font-bold text-[#E6EDF3] mt-0.5 block">
                    {diagnostics.limits.max_repo_mb} MB
                  </span>
                </div>
                <div className="p-3 rounded-md bg-[#0D1117] border border-[#21262D]">
                  <span className="text-[10px] text-[#8B949E] uppercase font-sans block">Max Files Scanned</span>
                  <span className="text-base font-bold text-[#E6EDF3] mt-0.5 block">
                    {diagnostics.limits.max_repo_files}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
