"use client";

import React, { useMemo, useState } from "react";
import {
  Search,
  Filter,
  ChevronRight,
  CheckCircle2,
  X,
} from "lucide-react";
import { Finding, Severity, AIDiagnosis } from "@/types/repomedic";
import { SeverityBadge, EvidenceQualityBadge } from "@/components/ui/Badge";
import { FindingDetailDrawer } from "./FindingDetailDrawer";

const SEVERITY_ORDER: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

interface FindingsListProps {
  findings: Finding[];
  diagnoses?: AIDiagnosis[];
}

export function FindingsList({ findings = [], diagnoses = [] }: FindingsListProps) {
  const [search, setSearch] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");
  const [selectedSource, setSelectedSource] = useState<string>("all");
  const [selectedQuality, setSelectedQuality] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"severity" | "path" | "title">("severity");
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  // Available sources from actual findings
  const sources = useMemo(() => {
    const s = new Set<string>();
    findings.forEach((f) => {
      if (f.source) s.add(f.source);
    });
    return Array.from(s).sort();
  }, [findings]);

  // Map finding_id -> AIDiagnosis
  const diagnosisMap = useMemo(() => {
    const map = new Map<string, AIDiagnosis>();
    (diagnoses || []).forEach((d) => {
      if (d.finding_id) map.set(d.finding_id, d);
    });
    return map;
  }, [diagnoses]);

  // Filter findings
  const filtered = useMemo(() => {
    return findings.filter((f) => {
      // Search
      const q = search.trim().toLowerCase();
      const matchesSearch =
        !q ||
        f.title?.toLowerCase().includes(q) ||
        f.rule_id?.toLowerCase().includes(q) ||
        f.file_path?.toLowerCase().includes(q) ||
        f.description?.toLowerCase().includes(q) ||
        f.id?.toLowerCase().includes(q);

      // Severity
      const matchesSev = selectedSeverity === "all" || f.severity === selectedSeverity;

      // Source
      const matchesSrc = selectedSource === "all" || f.source === selectedSource;

      // Evidence quality
      const matchesQuality = selectedQuality === "all" || f.evidence_quality === selectedQuality;

      return matchesSearch && matchesSev && matchesSrc && matchesQuality;
    });
  }, [findings, search, selectedSeverity, selectedSource, selectedQuality]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      if (sortBy === "severity") {
        const diff = (SEVERITY_ORDER[a.severity] ?? 5) - (SEVERITY_ORDER[b.severity] ?? 5);
        if (diff !== 0) return diff;
        return a.file_path.localeCompare(b.file_path);
      }
      if (sortBy === "path") {
        const diff = a.file_path.localeCompare(b.file_path);
        if (diff !== 0) return diff;
        return a.line_start - b.line_start;
      }
      return a.title.localeCompare(b.title);
    });
  }, [filtered, sortBy]);

  // Global clean state: no findings detected anywhere
  if (findings.length === 0) {
    return (
      <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-12 text-center shadow-xs">
        <div className="inline-flex p-3 rounded-full bg-[#3FB950]/10 text-[#3FB950] mb-3">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-[#E6EDF3]">Zero Findings Detected</h3>
        <p className="mt-1 text-xs text-[#8B949E] max-w-md mx-auto leading-relaxed">
          All active security scanner engines completed analysis without emitting actionable vulnerability findings in the candidate files.
        </p>
      </div>
    );
  }

  const hasActiveFilters =
    search.trim() !== "" ||
    selectedSeverity !== "all" ||
    selectedSource !== "all" ||
    selectedQuality !== "all";

  function handleResetFilters() {
    setSearch("");
    setSelectedSeverity("all");
    setSelectedSource("all");
    setSelectedQuality("all");
  }

  return (
    <div className="space-y-4">
      {/* Controls & Filter Bar */}
      <div className="p-3.5 rounded-lg border border-[#30363D] bg-[#161B22] space-y-3">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-[#8B949E] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search title, rule, path, or finding ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-8 py-1.5 rounded-md bg-[#0D1117] border border-[#30363D] text-xs text-[#E6EDF3] placeholder-[#6E7681] focus:outline-none focus:border-[#58A6FF] transition-colors"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8B949E] hover:text-[#E6EDF3]"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Quick Stats & Reset */}
          <div className="flex items-center justify-between md:justify-end gap-3 text-xs text-[#8B949E]">
            <span>
              Showing <strong className="text-[#E6EDF3]">{sorted.length}</strong> of {findings.length} findings
            </span>
            {hasActiveFilters && (
              <button
                onClick={handleResetFilters}
                className="text-xs text-[#58A6FF] hover:underline font-medium"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>

        {/* Filter Pills & Selectors */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#21262D]">
          {/* Severity Segmented Filter */}
          <div className="inline-flex rounded-md border border-[#30363D] bg-[#0D1117] p-0.5 text-xs">
            {["all", "critical", "high", "medium", "low", "info"].map((sev) => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-2.5 py-1 rounded text-[11px] capitalize font-medium transition-colors ${
                  selectedSeverity === sev
                    ? "bg-[#21262D] text-[#E6EDF3] shadow-xs"
                    : "text-[#8B949E] hover:text-[#E6EDF3]"
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Source Dropdown */}
          {sources.length > 1 && (
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="px-2.5 py-1 rounded-md bg-[#0D1117] border border-[#30363D] text-xs text-[#E6EDF3] focus:outline-none focus:border-[#58A6FF]"
            >
              <option value="all">All Engines ({sources.length})</option>
              {sources.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          )}

          {/* Evidence Quality Filter */}
          <select
            value={selectedQuality}
            onChange={(e) => setSelectedQuality(e.target.value)}
            className="px-2.5 py-1 rounded-md bg-[#0D1117] border border-[#30363D] text-xs text-[#E6EDF3] focus:outline-none focus:border-[#58A6FF]"
          >
            <option value="all">All Evidence Types</option>
            <option value="deterministic">Deterministic Check</option>
            <option value="ai_interpretation">AI Interpretation</option>
          </select>

          {/* Sort By */}
          <div className="ml-auto flex items-center gap-1.5 text-xs text-[#8B949E]">
            <span className="text-[11px]">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "severity" | "path" | "title")}
              className="px-2 py-1 rounded bg-[#0D1117] border border-[#30363D] text-xs text-[#E6EDF3] focus:outline-none focus:border-[#58A6FF]"
            >
              <option value="severity">Severity (High to Low)</option>
              <option value="path">File Path</option>
              <option value="title">Finding Title</option>
            </select>
          </div>
        </div>
      </div>

      {/* Filtered Empty State */}
      {sorted.length === 0 ? (
        <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-10 text-center">
          <Filter className="w-8 h-8 text-[#8B949E] mx-auto mb-2 opacity-50" />
          <h4 className="text-sm font-semibold text-[#E6EDF3]">No findings match active filters</h4>
          <p className="text-xs text-[#8B949E] mt-1 max-w-sm mx-auto">
            Try adjusting your search query, severity, or engine filter.
          </p>
          <button
            onClick={handleResetFilters}
            className="mt-3 inline-flex items-center px-3 py-1.5 rounded-md bg-[#21262D] hover:bg-[#30363D] text-xs text-[#E6EDF3] font-medium transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        /* Dense Technical Findings Table */
        <div className="border border-[#30363D] rounded-lg bg-[#161B22] overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-[#21262D] text-left text-xs">
              <thead className="bg-[#0D1117] text-[#8B949E] text-[11px] font-semibold uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-4 py-2.5 w-24">Severity</th>
                  <th scope="col" className="px-4 py-2.5">Finding & Rule</th>
                  <th scope="col" className="px-4 py-2.5">Location</th>
                  <th scope="col" className="px-4 py-2.5">Engine</th>
                  <th scope="col" className="px-4 py-2.5">Evidence Quality</th>
                  <th scope="col" className="px-4 py-2.5 text-right w-20">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#21262D]">
                {sorted.map((finding) => (
                  <tr
                    key={finding.id}
                    onClick={() => setSelectedFinding(finding)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setSelectedFinding(finding);
                      }
                    }}
                    tabIndex={0}
                    role="button"
                    aria-label={`Inspect ${finding.severity} finding: ${finding.title}`}
                    className="hover:bg-[#21262D]/60 transition-colors cursor-pointer group focus:outline-none focus:bg-[#21262D]"
                  >
                    <td className="px-4 py-3 align-top whitespace-nowrap">
                      <SeverityBadge severity={finding.severity} showIcon />
                    </td>

                    <td className="px-4 py-3 align-top">
                      <div className="space-y-0.5">
                        <div className="font-semibold text-xs text-[#E6EDF3] group-hover:text-[#58A6FF] transition-colors leading-snug">
                          {finding.title}
                        </div>
                        <div className="flex items-center gap-2 text-[11px] text-[#8B949E]">
                          <code className="font-mono text-[#8B949E]">{finding.rule_id}</code>
                          <span>&bull;</span>
                          <span className="font-mono text-[10px] text-[#6E7681]">#{finding.id}</span>
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-3 align-top font-mono text-[11px] text-[#8B949E] max-w-xs truncate">
                      <span className="text-[#58A6FF] hover:underline" title={finding.file_path}>
                        {finding.file_path}:{finding.line_start}
                      </span>
                    </td>

                    <td className="px-4 py-3 align-top text-xs text-[#E6EDF3] whitespace-nowrap">
                      <span className="font-mono text-[11px] text-[#8B949E]">{finding.source}</span>
                    </td>

                    <td className="px-4 py-3 align-top whitespace-nowrap">
                      <EvidenceQualityBadge quality={finding.evidence_quality} />
                    </td>

                    <td className="px-4 py-3 align-top text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFinding(finding);
                        }}
                        className="inline-flex items-center gap-1 text-[11px] text-[#8B949E] group-hover:text-[#58A6FF] font-medium"
                      >
                        <span>Inspect</span>
                        <ChevronRight className="w-3.5 h-3.5 text-[#8B949E] group-hover:text-[#58A6FF] transition-transform group-hover:translate-x-0.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Slide-Over Finding Inspector Drawer */}
      <FindingDetailDrawer
        finding={selectedFinding}
        aiDiagnosis={selectedFinding ? diagnosisMap.get(selectedFinding.id) : null}
        onClose={() => setSelectedFinding(null)}
      />
    </div>
  );
}
