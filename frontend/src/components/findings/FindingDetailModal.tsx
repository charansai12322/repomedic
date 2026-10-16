"use client";

import React from "react";
import { X, ShieldAlert, FileText, CheckCircle2, ExternalLink, Copy, Check, Sparkles } from "lucide-react";
import { Finding } from "@/types/repomedic";
import { SeverityBadge } from "@/components/ui/Badge";

interface FindingDetailModalProps {
  finding: Finding | null;
  onClose: () => void;
}

export function FindingDetailModal({ finding, onClose }: FindingDetailModalProps) {
  const [copied, setCopied] = React.useState(false);

  if (!finding) return null;

  function copyEvidence() {
    if (!finding?.evidence) return;
    navigator.clipboard.writeText(finding.evidence);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div
        className="bg-zinc-900 border border-zinc-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col animate-in fade-in zoom-in-95 duration-150"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-zinc-800 flex items-start justify-between bg-zinc-950/60 sticky top-0 z-10">
          <div className="flex items-start space-x-3 pr-4">
            <div className="mt-0.5">
              <SeverityBadge severity={finding.severity} />
            </div>
            <div>
              <h2 className="text-base font-bold text-zinc-100 leading-snug">
                {finding.title}
              </h2>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-400">
                <span>Rule: <code className="font-mono text-zinc-300">{finding.rule_id}</code></span>
                <span>&bull;</span>
                <span>Source: <strong className="text-zinc-300">{finding.source}</strong></span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5 text-xs text-zinc-300">
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-lg bg-zinc-950/50 border border-zinc-800/80">
            <div>
              <span className="block text-[10px] text-zinc-500 uppercase font-semibold">Location</span>
              <span className="font-mono text-zinc-200 font-medium truncate block mt-0.5">
                {finding.file_path}:{finding.line_start}
              </span>
            </div>
            <div>
              <span className="block text-[10px] text-zinc-500 uppercase font-semibold">Confidence</span>
              <span className="capitalize text-zinc-200 font-medium block mt-0.5">
                {finding.confidence}
              </span>
            </div>
            <div>
              <span className="block text-[10px] text-zinc-500 uppercase font-semibold">Evidence Quality</span>
              <span className="capitalize font-medium block mt-0.5 text-zinc-200 flex items-center gap-1">
                {finding.evidence_quality === "deterministic" ? (
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                ) : (
                  <Sparkles className="w-3 h-3 text-blue-400" />
                )}
                {finding.evidence_quality.replace("_", " ")}
              </span>
            </div>
            <div>
              <span className="block text-[10px] text-zinc-500 uppercase font-semibold">Finding ID</span>
              <span className="font-mono text-zinc-400 block mt-0.5">{finding.id}</span>
            </div>
          </div>

          {/* Description */}
          <div>
            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1.5">
              Vulnerability Description
            </h4>
            <p className="text-zinc-200 leading-relaxed bg-zinc-950/40 p-3 rounded border border-zinc-800/60">
              {finding.description}
            </p>
          </div>

          {/* Evidence Code Box */}
          {finding.evidence && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
                  Extracted Evidence (Sanitized)
                </h4>
                <button
                  onClick={copyEvidence}
                  className="inline-flex items-center space-x-1 text-[11px] text-zinc-400 hover:text-zinc-200 transition-colors"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? "Copied" : "Copy"}</span>
                </button>
              </div>
              <div className="rounded-lg overflow-hidden border border-zinc-800 bg-zinc-950">
                <pre className="p-3 font-mono text-[11px] text-indigo-300 overflow-x-auto leading-relaxed">
                  <code>{finding.evidence}</code>
                </pre>
              </div>
              <p className="mt-1 text-[10px] text-zinc-500">
                * Note: Raw credentials, keys, and tokens are permanently redacted server-side before display.
              </p>
            </div>
          )}

          {/* Remediation */}
          {finding.remediation && (
            <div>
              <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-1.5">
                Recommended Remediation
              </h4>
              <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-emerald-200 leading-relaxed">
                {finding.remediation}
              </div>
            </div>
          )}

          {/* References */}
          {finding.references && finding.references.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1.5">
                References & Citations
              </h4>
              <ul className="space-y-1">
                {finding.references.map((ref, idx) => (
                  <li key={idx} className="flex items-center space-x-1.5 text-zinc-400">
                    <ExternalLink className="w-3 h-3 text-zinc-500" />
                    {ref.startsWith("http") ? (
                      <a
                        href={ref}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-400 hover:underline truncate"
                      >
                        {ref}
                      </a>
                    ) : (
                      <span className="font-mono text-zinc-300">{ref}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-zinc-800 bg-zinc-950/40 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
