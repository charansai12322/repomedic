import React from "react";
import { CheckCircle2, XCircle, AlertCircle, MinusCircle, Clock } from "lucide-react";
import { ScannerHealth, ScannerStatus } from "@/types/repomedic";
import { StatusBadge } from "@/components/ui/Badge";

interface ScannerHealthTableProps {
  scanners: Record<string, ScannerHealth>;
}

export function ScannerHealthTable({ scanners }: ScannerHealthTableProps) {
  const scannerEntries = Object.entries(scanners || {});

  function getStatusIcon(status: ScannerStatus) {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-3.5 h-3.5 text-[#3FB950] shrink-0" />;
      case "failed":
        return <XCircle className="w-3.5 h-3.5 text-[#F85149] shrink-0" />;
      case "unavailable":
        return <AlertCircle className="w-3.5 h-3.5 text-[#D29922] shrink-0" />;
      case "skipped":
        return <MinusCircle className="w-3.5 h-3.5 text-[#6E7681] shrink-0" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-[#58A6FF] shrink-0" />;
    }
  }

  const engineLabels: Record<string, string> = {
    custom_rules: "Custom Security Rules",
    python_ast: "Python AST Analyzer",
    osv: "OSV Vulnerability DB",
    semgrep: "Semgrep Ruleset",
    git_history: "Git Commit History",
  };

  return (
    <div className="bg-[#161B22] border border-[#30363D] rounded-lg overflow-hidden shadow-xs">
      <div className="px-4 py-3 border-b border-[#21262D] bg-[#0D1117]/60 flex justify-between items-center">
        <h3 className="text-xs font-semibold text-[#E6EDF3] uppercase tracking-wider">
          Scanner Engine Telemetry
        </h3>
        <span className="text-[11px] font-mono text-[#8B949E]">
          {scannerEntries.length} engines configured
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[#21262D] text-left text-xs">
          <thead className="bg-[#0D1117]/40 text-[#8B949E] text-[11px] font-semibold uppercase">
            <tr>
              <th scope="col" className="px-4 py-2.5">Engine</th>
              <th scope="col" className="px-4 py-2.5">Status</th>
              <th scope="col" className="px-4 py-2.5">Policy</th>
              <th scope="col" className="px-4 py-2.5">Findings</th>
              <th scope="col" className="px-4 py-2.5">Duration</th>
              <th scope="col" className="px-4 py-2.5">Diagnostic Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#21262D]">
            {scannerEntries.map(([name, health]) => (
              <tr key={name} className="hover:bg-[#21262D]/50 transition-colors">
                <td className="px-4 py-2.5 font-medium text-[#E6EDF3]">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(health.status)}
                    <div>
                      <span className="font-semibold text-xs block text-[#E6EDF3]">
                        {engineLabels[name] || name}
                      </span>
                      <span className="font-mono text-[10px] text-[#8B949E]">{name}</span>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={health.status} />
                </td>
                <td className="px-4 py-2.5 text-xs">
                  {health.required ? (
                    <span className="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-medium bg-[#D29922]/10 text-[#D29922] border border-[#D29922]/30">
                      Required
                    </span>
                  ) : (
                    <span className="text-[#8B949E] text-[11px]">Optional</span>
                  )}
                </td>
                <td className="px-4 py-2.5 font-mono text-xs text-[#E6EDF3]">
                  {health.finding_count}
                </td>
                <td className="px-4 py-2.5 font-mono text-xs text-[#8B949E]">
                  {health.duration_ms} ms
                </td>
                <td className="px-4 py-2.5 text-xs text-[#8B949E] max-w-sm truncate">
                  {health.error_message ||
                    (health.status === "skipped"
                      ? "Skipped by scan configuration"
                      : "Engine verified and completed")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
