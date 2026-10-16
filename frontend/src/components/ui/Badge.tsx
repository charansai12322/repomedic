import React from "react";
import { Severity, ScannerStatus, AuditStatus, JobState, EvidenceQuality } from "@/types/repomedic";
import { ShieldAlert, AlertTriangle, AlertCircle, Info, Sparkles, CheckCircle2 } from "lucide-react";

interface SeverityBadgeProps {
  severity: Severity | string;
  className?: string;
  showIcon?: boolean;
}

export function SeverityBadge({ severity, className = "", showIcon = false }: SeverityBadgeProps) {
  const sev = (severity || "info").toLowerCase() as Severity;

  const styles: Record<Severity, { bg: string; text: string; border: string; label: string }> = {
    critical: {
      bg: "bg-[#F85149]/10",
      text: "text-[#F85149]",
      border: "border-[#F85149]/30",
      label: "Critical",
    },
    high: {
      bg: "bg-[#F0883E]/10",
      text: "text-[#F0883E]",
      border: "border-[#F0883E]/30",
      label: "High",
    },
    medium: {
      bg: "bg-[#D29922]/10",
      text: "text-[#D29922]",
      border: "border-[#D29922]/30",
      label: "Medium",
    },
    low: {
      bg: "bg-[#58A6FF]/10",
      text: "text-[#58A6FF]",
      border: "border-[#58A6FF]/30",
      label: "Low",
    },
    info: {
      bg: "bg-[#21262D]",
      text: "text-[#8B949E]",
      border: "border-[#30363D]",
      label: "Info",
    },
  };

  const current = styles[sev] || styles.info;

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-medium border leading-none ${current.bg} ${current.text} ${current.border} ${className}`}
    >
      {showIcon && (
        <span className="shrink-0" aria-hidden="true">
          {sev === "critical" && <ShieldAlert className="w-3 h-3" />}
          {sev === "high" && <AlertTriangle className="w-3 h-3" />}
          {sev === "medium" && <AlertCircle className="w-3 h-3" />}
          {sev === "low" && <Info className="w-3 h-3" />}
          {sev === "info" && <Info className="w-3 h-3" />}
        </span>
      )}
      <span>{current.label}</span>
    </span>
  );
}

interface StatusBadgeProps {
  status: ScannerStatus | AuditStatus | JobState | string;
  className?: string;
}

export function StatusBadge({ status, className = "" }: StatusBadgeProps) {
  const normalized = (status || "").toLowerCase();

  let styles = "bg-[#21262D] text-[#8B949E] border-[#30363D]";
  let dotColor = "bg-[#8B949E]";

  if (["completed", "complete", "ready", "ok"].includes(normalized)) {
    styles = "bg-[#3FB950]/10 text-[#3FB950] border-[#3FB950]/30";
    dotColor = "bg-[#3FB950]";
  } else if (["running", "in_progress"].includes(normalized)) {
    styles = "bg-[#58A6FF]/10 text-[#58A6FF] border-[#58A6FF]/30";
    dotColor = "bg-[#58A6FF] animate-pulse";
  } else if (["partial", "skipped"].includes(normalized)) {
    styles = "bg-[#D29922]/10 text-[#D29922] border-[#D29922]/30";
    dotColor = "bg-[#D29922]";
  } else if (["queued", "pending"].includes(normalized)) {
    styles = "bg-[#21262D] text-[#8B949E] border-[#30363D]";
    dotColor = "bg-[#8B949E]";
  } else if (["failed", "unavailable", "error"].includes(normalized)) {
    styles = "bg-[#F85149]/10 text-[#F85149] border-[#F85149]/30";
    dotColor = "bg-[#F85149]";
  } else if (["cancelled"].includes(normalized)) {
    styles = "bg-[#21262D] text-[#8B949E] border-[#30363D]";
    dotColor = "bg-[#6E7681]";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium capitalize border leading-none ${styles} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} aria-hidden="true" />
      <span>{status}</span>
    </span>
  );
}

interface EvidenceQualityBadgeProps {
  quality: EvidenceQuality | string;
  className?: string;
}

export function EvidenceQualityBadge({ quality, className = "" }: EvidenceQualityBadgeProps) {
  const isDeterministic = quality === "deterministic";

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border leading-none ${
        isDeterministic
          ? "bg-[#3FB950]/10 text-[#3FB950] border-[#3FB950]/25"
          : "bg-[#58A6FF]/10 text-[#58A6FF] border-[#58A6FF]/25"
      } ${className}`}
      title={
        isDeterministic
          ? "Deterministic scanner check with validated location evidence"
          : "AI-assisted triage interpretation and remediation"
      }
    >
      {isDeterministic ? (
        <CheckCircle2 className="w-2.5 h-2.5 shrink-0" aria-hidden="true" />
      ) : (
        <Sparkles className="w-2.5 h-2.5 shrink-0" aria-hidden="true" />
      )}
      <span>{isDeterministic ? "Scanner Evidence" : "AI Interpretation"}</span>
    </span>
  );
}
