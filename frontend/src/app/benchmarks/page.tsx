"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
  ShieldCheck,
  FileText,
  Activity,
  Layers,
  ArrowRight,
} from "lucide-react";
import { BenchmarkReport, FixtureEvaluation } from "@/types/repomedic";
import { getLatestBenchmark } from "@/lib/api";
import { StatusBadge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { formatDurationMs } from "@/lib/formatters";

export default function BenchmarksPage() {
  const [data, setData] = useState<BenchmarkReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBenchmark = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setError(null);
    try {
      const res = await getLatestBenchmark();
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load benchmark results from backend.";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    getLatestBenchmark()
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Failed to load benchmark results from backend.";
          setError(msg);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header (Section 11.1) */}
      <PageHeader
        breadcrumbs={[
          { label: "Overview", href: "/" },
          { label: "Benchmarks" },
        ]}
        title="Benchmarks"
        description="Evaluate scanner coverage, detection quality, and execution performance against reproducible test fixtures."
        actions={
          <button
            onClick={() => loadBenchmark(true)}
            disabled={refreshing || loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-[#161B22] hover:bg-[#21262D] text-[#8B949E] hover:text-[#E6EDF3] border border-[#30363D] transition-colors disabled:opacity-50"
            title="Refresh benchmark data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-[#58A6FF]" : ""}`} />
            <span>Refresh Run</span>
          </button>
        }
      />

      {loading ? (
        <div className="py-20 text-center space-y-3">
          <RefreshCw className="w-6 h-6 animate-spin text-[#58A6FF] mx-auto" />
          <p className="text-xs text-[#8B949E]">Loading benchmark scorecard...</p>
        </div>
      ) : error || !data ? (
        /* Empty State (Section 11.3) */
        <div className="max-w-xl mx-auto py-10 text-center space-y-4">
          <div className="p-8 rounded-lg border border-[#30363D] bg-[#161B22] space-y-3 shadow-xs">
            <BarChart3 className="w-10 h-10 text-[#6E7681] mx-auto" />
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-[#E6EDF3]">No Benchmark Results Recorded</h3>
              <p className="text-xs text-[#8B949E] leading-relaxed">
                RepoMedic evaluates static detection against 16 synthetic fixtures and negative controls. Run the offline benchmark runner to generate authoritative metrics:
              </p>
            </div>
            <div className="p-3 rounded-md bg-[#010409] border border-[#21262D] max-w-sm mx-auto text-left font-mono text-xs text-[#E6EDF3]">
              <code>python backend/benchmarks/runner.py</code>
            </div>
            <div className="pt-2">
              <button
                onClick={() => loadBenchmark()}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-[#21262D] hover:bg-[#30363D] text-xs font-semibold text-[#E6EDF3] transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Check Again</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Real Benchmark Presentation (Section 11.2 - 11.4) */
        <div className="space-y-6">
          {/* Metadata Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-md bg-[#161B22] border border-[#21262D] text-xs text-[#8B949E]">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#58A6FF]" />
              <span>
                Run Timestamp:{" "}
                <strong className="text-[#E6EDF3] font-mono">
                  {data.timestamp_utc ? new Date(data.timestamp_utc).toUTCString() : "Offline test"}
                </strong>
              </span>
            </div>
            <div className="flex items-center gap-3 font-mono text-[11px]">
              <span>{data.total_fixtures} Total Fixtures</span>
              <span>&bull;</span>
              <span>Avg Latency: {data.average_scan_duration_ms ? data.average_scan_duration_ms.toFixed(1) : 0}ms</span>
            </div>
          </div>

          {/* Primary Accuracy Metric Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Precision */}
            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-mono font-medium text-[#8B949E]">
                  Precision
                </span>
                <span className="text-[10px] text-[#6E7681] font-mono">TP / (TP + FP)</span>
              </div>
              <div className="text-2xl font-bold font-mono text-[#3FB950] mt-1">
                {data.precision !== null ? `${(data.precision * 100).toFixed(1)}%` : "N/A"}
              </div>
              <div className="text-[11px] text-[#8B949E] mt-1">
                {data.true_positives} TP &bull; {data.false_positives} FP
              </div>
            </div>

            {/* Recall */}
            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-mono font-medium text-[#8B949E]">
                  Recall (Sensitivity)
                </span>
                <span className="text-[10px] text-[#6E7681] font-mono">TP / (TP + FN)</span>
              </div>
              <div className="text-2xl font-bold font-mono text-[#58A6FF] mt-1">
                {data.recall !== null ? `${(data.recall * 100).toFixed(1)}%` : "N/A"}
              </div>
              <div className="text-[11px] text-[#8B949E] mt-1">
                {data.true_positives} TP &bull; {data.false_negatives} FN
              </div>
            </div>

            {/* False Positive Rate */}
            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-mono font-medium text-[#8B949E]">
                  False Positive Rate
                </span>
                <span className="text-[10px] text-[#6E7681] font-mono">FP / (FP + TN)</span>
              </div>
              <div className="text-2xl font-bold font-mono text-[#E6EDF3] mt-1">
                {data.false_positive_rate !== null ? `${(data.false_positive_rate * 100).toFixed(1)}%` : "N/A"}
              </div>
              <div className="text-[11px] text-[#8B949E] mt-1">
                {data.true_negatives} clean negative controls
              </div>
            </div>

            {/* F1 Score */}
            <div className="p-4 rounded-lg bg-[#161B22] border border-[#30363D] shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-mono font-medium text-[#8B949E]">
                  F1 Harmonic Mean
                </span>
                <span className="text-[10px] text-[#6E7681] font-mono">2*(P*R)/(P+R)</span>
              </div>
              <div className="text-2xl font-bold font-mono text-[#E6EDF3] mt-1">
                {data.f1_score !== null ? `${(data.f1_score * 100).toFixed(1)}%` : "N/A"}
              </div>
              <div className="text-[11px] text-[#8B949E] mt-1">
                Balanced accuracy benchmark
              </div>
            </div>
          </div>

          {/* Secondary Operational Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-lg bg-[#161B22] border border-[#30363D]">
              <span className="text-[10px] uppercase font-mono text-[#8B949E] block">AI Citation Validity</span>
              <span className="text-lg font-bold font-mono text-[#58A6FF] mt-0.5 block">
                {(data.ai_citation_validity * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-[#6E7681]">Verified against scanner findings</span>
            </div>

            <div className="p-3.5 rounded-lg bg-[#161B22] border border-[#30363D]">
              <span className="text-[10px] uppercase font-mono text-[#8B949E] block">Median Latency</span>
              <span className="text-lg font-bold font-mono text-[#E6EDF3] mt-0.5 block">
                {data.median_scan_duration_ms ? data.median_scan_duration_ms.toFixed(1) : 0}ms
              </span>
              <span className="text-[10px] text-[#6E7681]">Per-fixture execution</span>
            </div>

            <div className="p-3.5 rounded-lg bg-[#161B22] border border-[#30363D]">
              <span className="text-[10px] uppercase font-mono text-[#8B949E] block">Scanner Availability</span>
              <span className="text-lg font-bold font-mono text-[#3FB950] mt-0.5 block">
                {(data.scanner_availability_rate * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-[#6E7681]">Engines completed</span>
            </div>

            <div className="p-3.5 rounded-lg bg-[#161B22] border border-[#30363D]">
              <span className="text-[10px] uppercase font-mono text-[#8B949E] block">Partial Audit Rate</span>
              <span className="text-lg font-bold font-mono text-[#D29922] mt-0.5 block">
                {(data.partial_audit_rate * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-[#6E7681]">Fixtures with degraded subsystems</span>
            </div>
          </div>

          {/* Clean Accuracy Visual Comparison (Section 11.3) */}
          <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] space-y-4 shadow-xs">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8B949E]">
              Metric Scale Comparison
            </h3>

            <div className="space-y-3 text-xs">
              {/* Precision Bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-[#E6EDF3]">Precision</span>
                  <span className="font-mono text-[#3FB950]">
                    {data.precision !== null ? `${(data.precision * 100).toFixed(1)}%` : "0%"}
                  </span>
                </div>
                <div className="w-full bg-[#0D1117] h-2 rounded-full overflow-hidden border border-[#21262D]">
                  <div
                    className="h-full bg-[#3FB950] rounded-full"
                    style={{ width: `${Math.min(Math.max((data.precision || 0) * 100, 0), 100)}%` }}
                  />
                </div>
              </div>

              {/* Recall Bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-[#E6EDF3]">Recall</span>
                  <span className="font-mono text-[#58A6FF]">
                    {data.recall !== null ? `${(data.recall * 100).toFixed(1)}%` : "0%"}
                  </span>
                </div>
                <div className="w-full bg-[#0D1117] h-2 rounded-full overflow-hidden border border-[#21262D]">
                  <div
                    className="h-full bg-[#58A6FF] rounded-full"
                    style={{ width: `${Math.min(Math.max((data.recall || 0) * 100, 0), 100)}%` }}
                  />
                </div>
              </div>

              {/* False Positive Rate Bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-[#E6EDF3]">False Positive Rate</span>
                  <span className="font-mono text-[#F0883E]">
                    {data.false_positive_rate !== null ? `${(data.false_positive_rate * 100).toFixed(1)}%` : "0%"}
                  </span>
                </div>
                <div className="w-full bg-[#0D1117] h-2 rounded-full overflow-hidden border border-[#21262D]">
                  <div
                    className="h-full bg-[#F0883E] rounded-full"
                    style={{ width: `${Math.min(Math.max((data.false_positive_rate || 0) * 100, 0), 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Fixture Breakdown Table if evaluations exist */}
          {data.evaluations && data.evaluations.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8B949E]">
                  Fixture Evaluation Breakdown ({data.evaluations.length})
                </h3>
              </div>

              <div className="border border-[#30363D] rounded-lg bg-[#161B22] overflow-hidden shadow-xs">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-[#21262D] text-left text-xs">
                    <thead className="bg-[#0D1117] text-[#8B949E] text-[11px] font-semibold uppercase tracking-wider">
                      <tr>
                        <th scope="col" className="px-4 py-2.5">Fixture ID & Name</th>
                        <th scope="col" className="px-4 py-2.5">Type</th>
                        <th scope="col" className="px-4 py-2.5">TP</th>
                        <th scope="col" className="px-4 py-2.5">FP</th>
                        <th scope="col" className="px-4 py-2.5">FN</th>
                        <th scope="col" className="px-4 py-2.5">TN</th>
                        <th scope="col" className="px-4 py-2.5">Latency</th>
                        <th scope="col" className="px-4 py-2.5 text-right">Audit Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#21262D]">
                      {data.evaluations.map((ev) => (
                        <tr key={ev.fixture_id} className="hover:bg-[#21262D]/50 transition-colors">
                          <td className="px-4 py-2.5 font-medium text-[#E6EDF3]">
                            <div className="font-semibold text-xs">{ev.name}</div>
                            <span className="font-mono text-[10px] text-[#8B949E]">{ev.fixture_id}</span>
                          </td>
                          <td className="px-4 py-2.5 text-[11px]">
                            {ev.is_negative_control ? (
                              <span className="text-[#3FB950] font-medium">Negative Control</span>
                            ) : (
                              <span className="text-[#58A6FF] font-medium">Target Fixture</span>
                            )}
                          </td>
                          <td className="px-4 py-2.5 font-mono text-[#3FB950]">{ev.tp}</td>
                          <td className="px-4 py-2.5 font-mono text-[#F85149]">{ev.fp}</td>
                          <td className="px-4 py-2.5 font-mono text-[#D29922]">{ev.fn}</td>
                          <td className="px-4 py-2.5 font-mono text-[#8B949E]">{ev.tn}</td>
                          <td className="px-4 py-2.5 font-mono text-[#8B949E]">{ev.duration_ms}ms</td>
                          <td className="px-4 py-2.5 text-right">
                            <StatusBadge status={ev.audit_status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Methodology Note (Section 11.4) */}
          <div className="p-4 rounded-lg bg-[#0D1117] border border-[#21262D] text-xs text-[#8B949E] space-y-1">
            <span className="font-semibold text-[#E6EDF3] block">Benchmark Methodology & Limitations</span>
            <p className="leading-relaxed text-[11px]">
              Benchmark results are evaluated against versioned synthetic test fixtures with known ground-truth labels and negative controls. While these metrics establish engine precision and recall within controlled parameters, they do not guarantee real-world immunity against novel, zero-day, or multi-vector vulnerabilities.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
