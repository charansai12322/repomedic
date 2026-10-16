"use client";

import React, { useEffect, useRef } from "react";
import {
  X,
  Copy,
  Check,
  ExternalLink,
  ShieldAlert,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  ArrowUpRight,
  Info,
} from "lucide-react";
import { Finding, AIDiagnosis } from "@/types/repomedic";
import { SeverityBadge, EvidenceQualityBadge } from "@/components/ui/Badge";
import { redactSensitiveString } from "@/lib/formatters";

interface FindingDetailDrawerProps {
  finding: Finding | null;
  aiDiagnosis?: AIDiagnosis | null;
  onClose: () => void;
}

export function FindingDetailDrawer({
  finding,
  aiDiagnosis,
  onClose,
}: FindingDetailDrawerProps) {
  const [copied, setCopied] = React.useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Keyboard navigation: Escape key closes drawer
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }
    if (finding) {
      window.addEventListener("keydown", handleKeyDown);
      closeButtonRef.current?.focus();
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [finding, onClose]);

  if (!finding) return null;

  function handleCopyEvidence() {
    if (!finding?.evidence) return;
    const sanitized = redactSensitiveString(finding.evidence);
    navigator.clipboard.writeText(sanitized);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // Safe external URL verification
  function isSafeUrl(urlStr: string): boolean {
    try {
      const parsed = new URL(urlStr);
      return parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch {
      return false;
    }
  }

  const sanitizedEvidence = redactSensitiveString(finding.evidence || "");
  const evidenceLines = sanitizedEvidence ? sanitizedEvidence.split("\n") : [];
  const startLine = finding.line_start || 1;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="finding-drawer-title">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-6 sm:pl-10">
        <div
          ref={drawerRef}
          className="w-screen max-w-lg md:max-w-xl bg-[#161B22] border-l border-[#30363D] shadow-2xl flex flex-col justify-between overflow-hidden animate-in slide-in-from-right duration-200"
        >
          {/* Drawer Header */}
          <div className="px-5 py-4 border-b border-[#21262D] bg-[#0D1117] flex items-start justify-between gap-3 sticky top-0 z-10">
            <div className="space-y-1.5 flex-1 min-w-0 pr-2">
              <div className="flex flex-wrap items-center gap-2">
                <SeverityBadge severity={finding.severity} showIcon />
                <EvidenceQualityBadge quality={finding.evidence_quality} />
                <span className="text-[10px] font-mono text-[#8B949E] px-1.5 py-0.5 rounded bg-[#21262D] border border-[#30363D]">
                  {finding.id}
                </span>
              </div>
              <h2
                id="finding-drawer-title"
                className="text-base font-semibold text-[#E6EDF3] leading-snug break-words"
              >
                {finding.title}
              </h2>
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-[#8B949E]">
                <span>
                  Rule: <code className="font-mono text-[#E6EDF3]">{finding.rule_id}</code>
                </span>
                <span>&bull;</span>
                <span>
                  Engine: <strong className="text-[#E6EDF3]">{finding.source}</strong>
                </span>
              </div>
            </div>

            <button
              ref={closeButtonRef}
              onClick={onClose}
              className="p-1.5 rounded-md text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#21262D] transition-colors focus:outline-none focus:ring-1 focus:ring-[#58A6FF]"
              aria-label="Close finding inspector"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Scrollable Body */}
          <div className="flex-1 overflow-y-auto p-5 space-y-6 text-xs text-[#E6EDF3]">
            {/* Location & Metadata Bar */}
            <div className="grid grid-cols-2 gap-3 p-3 rounded-md bg-[#0D1117] border border-[#21262D] font-mono text-[11px]">
              <div>
                <span className="block text-[10px] text-[#8B949E] uppercase font-sans font-semibold">
                  File Path
                </span>
                <span className="text-[#58A6FF] block truncate mt-0.5" title={finding.file_path}>
                  {finding.file_path}
                </span>
              </div>
              <div>
                <span className="block text-[10px] text-[#8B949E] uppercase font-sans font-semibold">
                  Line Span
                </span>
                <span className="text-[#E6EDF3] block mt-0.5">
                  Lines {finding.line_start} &ndash; {finding.line_end}
                </span>
              </div>
              <div>
                <span className="block text-[10px] text-[#8B949E] uppercase font-sans font-semibold">
                  Assessment Confidence
                </span>
                <span className="capitalize text-[#E6EDF3] block mt-0.5">
                  {finding.confidence}
                </span>
              </div>
              <div>
                <span className="block text-[10px] text-[#8B949E] uppercase font-sans font-semibold">
                  Corroboration
                </span>
                <span className="text-[#8B949E] block mt-0.5">
                  {finding.corroborating_sources && finding.corroborating_sources.length > 0
                    ? finding.corroborating_sources.join(", ")
                    : "Primary check only"}
                </span>
              </div>
            </div>

            {/* Vulnerability Explanation */}
            <section className="space-y-1.5">
              <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider">
                Vulnerability Assessment
              </h3>
              <div className="p-3.5 rounded-md bg-[#0D1117] border border-[#21262D] text-[#E6EDF3] leading-relaxed whitespace-pre-wrap">
                {finding.description}
              </div>
            </section>

            {/* Sanitized Code Evidence */}
            {sanitizedEvidence && (
              <section className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5 text-[#58A6FF]" />
                    <span>Scanner Code Evidence</span>
                  </h3>
                  <button
                    onClick={handleCopyEvidence}
                    className="inline-flex items-center gap-1 text-[11px] font-mono text-[#8B949E] hover:text-[#E6EDF3] px-2 py-0.5 rounded hover:bg-[#21262D] transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-[#3FB950]" />
                        <span className="text-[#3FB950]">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="rounded-md border border-[#30363D] bg-[#010409] overflow-hidden text-xs font-mono">
                  <div className="px-3 py-1.5 bg-[#0D1117] border-b border-[#21262D] text-[10px] text-[#8B949E] flex items-center justify-between">
                    <span>{finding.file_path}:{finding.line_start}</span>
                    <span className="text-[#3FB950] font-sans font-medium text-[9px] uppercase tracking-wide">
                      Redacted
                    </span>
                  </div>
                  <div className="p-3 overflow-x-auto text-[11px] leading-snug">
                    <pre className="table w-full">
                      {evidenceLines.map((line, idx) => (
                        <div key={idx} className="table-row">
                          <span className="table-cell select-none pr-3 text-[#6E7681] text-right font-mono">
                            {startLine + idx}
                          </span>
                          <span className="table-cell whitespace-pre text-[#E6EDF3]">
                            {line || " "}
                          </span>
                        </div>
                      ))}
                    </pre>
                  </div>
                </div>
              </section>
            )}

            {/* AI Triage & Explanation (Section 10.3 / 10.4) */}
            {aiDiagnosis && (
              <section className="space-y-2 p-3.5 rounded-md border border-[#58A6FF]/30 bg-[#58A6FF]/5">
                <div className="flex items-center justify-between border-b border-[#58A6FF]/20 pb-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-[#58A6FF] uppercase tracking-wider">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>AI Triage Diagnosis</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {aiDiagnosis.likely_false_positive && (
                      <span className="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-semibold bg-[#D29922]/20 text-[#D29922] border border-[#D29922]/40">
                        Likely False Positive
                      </span>
                    )}
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#21262D] text-[#8B949E] border border-[#30363D]">
                      Priority {aiDiagnosis.priority}/5
                    </span>
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-[10px] uppercase font-mono tracking-wide text-[#8B949E] font-semibold block">
                      Why It Matters (Impact Assessment)
                    </span>
                    <p className="text-[#E6EDF3] mt-0.5 leading-relaxed">
                      {aiDiagnosis.why_it_matters}
                    </p>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase font-mono tracking-wide text-[#8B949E] font-semibold block">
                      Suggested Fix (AI Remediation Guidance)
                    </span>
                    <p className="text-[#E6EDF3] mt-0.5 leading-relaxed font-mono text-[11px] bg-[#0D1117] p-2.5 rounded border border-[#21262D]">
                      {aiDiagnosis.fix}
                    </p>
                  </div>
                </div>
              </section>
            )}

            {/* Deterministic Scanner Remediation */}
            {finding.remediation && (!aiDiagnosis || finding.remediation !== aiDiagnosis.fix) && (
              <section className="space-y-1.5">
                <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider">
                  Recommended Scanner Remediation
                </h3>
                <div className="p-3.5 rounded-md bg-[#0D1117] border border-[#21262D] text-[#E6EDF3] leading-relaxed">
                  {finding.remediation}
                </div>
              </section>
            )}

            {/* Citations & External References */}
            {finding.references && finding.references.length > 0 && (
              <section className="space-y-1.5">
                <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider">
                  References & External Citations
                </h3>
                <ul className="space-y-1 font-mono text-[11px]">
                  {finding.references.map((ref, idx) => {
                    const isLink = isSafeUrl(ref);
                    return (
                      <li key={idx} className="flex items-center gap-1.5 text-[#58A6FF] truncate">
                        {isLink ? (
                          <a
                            href={ref}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline flex items-center gap-1 truncate"
                          >
                            <span className="truncate">{ref}</span>
                            <ArrowUpRight className="w-3 h-3 shrink-0" />
                          </a>
                        ) : (
                          <span className="text-[#8B949E]">{ref}</span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </section>
            )}
          </div>

          {/* Drawer Footer */}
          <div className="px-5 py-3 border-t border-[#21262D] bg-[#0D1117] flex items-center justify-between text-xs text-[#8B949E]">
            <span className="font-mono text-[11px]">Fingerprint: {finding.fingerprint || finding.id}</span>
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded bg-[#21262D] hover:bg-[#30363D] text-[#E6EDF3] font-medium transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
