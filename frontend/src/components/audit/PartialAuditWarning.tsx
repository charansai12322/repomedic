import React from "react";
import { AlertTriangle, AlertOctagon, XCircle } from "lucide-react";
import { ScanHealthSummary } from "@/types/repomedic";

interface PartialAuditWarningProps {
  scanHealth: ScanHealthSummary;
}

export function PartialAuditWarning({ scanHealth }: PartialAuditWarningProps) {
  if (!scanHealth.partial_audit && scanHealth.audit_status === "complete") {
    return null;
  }

  const isFailed = scanHealth.audit_status === "failed";

  // Find required scanners that failed or were unavailable
  const failedRequired = Object.entries(scanHealth.scanners || {}).filter(
    ([_, h]) => h.required && ["failed", "unavailable"].includes(h.status)
  );

  return (
    <div
      role="alert"
      className={`rounded-lg border p-4 mb-6 shadow-xs ${
        isFailed
          ? "border-[#F85149]/40 bg-[#F85149]/10 text-[#E6EDF3]"
          : "border-[#D29922]/40 bg-[#D29922]/10 text-[#E6EDF3]"
      }`}
    >
      <div className="flex items-start space-x-3">
        <div
          className={`p-1 rounded shrink-0 mt-0.5 ${
            isFailed ? "text-[#F85149]" : "text-[#D29922]"
          }`}
          aria-hidden="true"
        >
          {isFailed ? <AlertOctagon className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#E6EDF3]">
              {isFailed ? "Audit Execution Failed" : "Partial Security Audit Warning"}
            </h3>
            <span
              className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border leading-none font-semibold ${
                isFailed
                  ? "bg-[#F85149]/20 text-[#F85149] border-[#F85149]/30"
                  : "bg-[#D29922]/20 text-[#D29922] border-[#D29922]/30"
              }`}
            >
              {isFailed ? "All Required Scanners Failed" : "Incomplete Coverage"}
            </span>
          </div>

          <p className="mt-1 text-xs text-[#8B949E] leading-relaxed">
            {isFailed
              ? "All mandatory security engines failed or timed out during execution. Collected findings are incomplete and cannot be used for compliance or safety certification."
              : "One or more mandatory security engines failed or were unavailable. This report does not represent a complete audit. Successfully collected findings remain available below."}
          </p>

          {failedRequired.length > 0 && (
            <div className="mt-3 text-xs bg-[#161B22] border border-[#30363D] rounded p-2.5 space-y-1">
              <span className="font-semibold text-[#E6EDF3]">Failed Required Scanner Engines:</span>
              <ul className="list-disc list-inside space-y-0.5 text-[#8B949E] font-mono text-[11px]">
                {failedRequired.map(([name, h]) => (
                  <li key={name}>
                    <span className="text-[#E6EDF3] font-semibold">{name}</span>: status is{" "}
                    <span className="uppercase text-[#F85149] font-bold">{h.status}</span>
                    {h.error_code && <span> [{h.error_code}]</span>}
                    {h.error_message && <span> &mdash; {h.error_message}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {scanHealth.degraded_reasons && scanHealth.degraded_reasons.length > 0 && (
            <div className="mt-2 text-[11px] text-[#8B949E] space-y-0.5">
              {scanHealth.degraded_reasons.map((reason, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <span
                    className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      isFailed ? "bg-[#F85149]" : "bg-[#D29922]"
                    }`}
                  />
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
