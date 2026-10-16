"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FolderGit2,
  History,
  Sparkles,
  ArrowRight,
  Loader2,
  AlertCircle,
  Info,
  ShieldCheck,
  Lock,
} from "lucide-react";
import { submitScan } from "@/lib/api";
import { validateGitRepoUrl } from "@/lib/formatters";
import { PageHeader } from "@/components/layout/PageHeader";

export default function NewAuditPage() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState("");
  const [enableGitHistory, setEnableGitHistory] = useState(false);
  const [enableAi, setEnableAi] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;

    setError(null);
    const trimmed = repoUrl.trim();

    // Client-side validation matching backend contract
    const validation = validateGitRepoUrl(trimmed);
    if (!validation.valid) {
      setError(validation.error || "Please provide a valid public repository URL.");
      return;
    }

    if (!trimmed.startsWith("https://github.com/")) {
      setError("Only public GitHub repositories over HTTPS are currently supported (e.g. https://github.com/owner/repo).");
      return;
    }

    const segments = trimmed.replace("https://github.com/", "").split("/").filter(Boolean);
    if (segments.length < 2) {
      setError("Please specify both owner and repository name (e.g. https://github.com/owner/repository).");
      return;
    }

    setSubmitting(true);
    try {
      const res = await submitScan({
        repo_url: trimmed,
        enable_git_history: enableGitHistory,
        enable_ai: enableAi,
      });

      // Immediate redirect to live progress polling
      router.push(`/audits/${res.job_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to submit repository for auditing. Please verify backend status and try again.";
      setError(msg);
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Page Header (Section 6.1) */}
      <PageHeader
        breadcrumbs={[
          { label: "Overview", href: "/" },
          { label: "New audit" },
        ]}
        title="Start an audit"
        description="Inspect a repository using the configured security scanners."
      />

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="rounded-lg border border-[#30363D] bg-[#161B22] p-5 sm:p-6 space-y-5 shadow-xs">
          {/* Error Banner */}
          {error && (
            <div className="p-3 rounded-md bg-[#F85149]/10 border border-[#F85149]/30 text-xs text-[#F85149] flex items-start gap-2.5" role="alert">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold block">Submission Error</span>
                <span className="mt-0.5 block leading-relaxed">{error}</span>
              </div>
            </div>
          )}

          {/* Repository Field (Section 6.2) */}
          <div className="space-y-1.5">
            <label htmlFor="repoUrl" className="block text-xs font-semibold text-[#E6EDF3]">
              Repository URL <span className="text-[#F85149]">*</span>
            </label>
            <div className="relative">
              <FolderGit2 className="w-4 h-4 text-[#8B949E] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                id="repoUrl"
                type="url"
                required
                disabled={submitting}
                placeholder="https://github.com/owner/repository"
                value={repoUrl}
                onChange={(e) => {
                  setRepoUrl(e.target.value);
                  if (error) setError(null);
                }}
                className="w-full pl-9 pr-3 py-2 rounded-md bg-[#0D1117] border border-[#30363D] text-xs font-mono text-[#E6EDF3] placeholder-[#6E7681] focus:outline-none focus:border-[#58A6FF] transition-colors disabled:opacity-50"
              />
            </div>
            <p className="text-[11px] text-[#8B949E] leading-relaxed">
              Public HTTPS GitHub repository coordinate. Target code is inspected strictly via static analysis and is never executed or built.
            </p>
          </div>

          {/* Scan Options (Section 6.3) */}
          <div className="space-y-3 pt-3 border-t border-[#21262D]">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#8B949E]">
              Scan options
            </h3>

            {/* AI Triage Checkbox */}
            <label className="flex items-start gap-3 p-3 rounded-md bg-[#0D1117] border border-[#21262D] cursor-pointer hover:border-[#30363D] transition-colors">
              <input
                type="checkbox"
                checked={enableAi}
                onChange={(e) => setEnableAi(e.target.checked)}
                disabled={submitting}
                className="mt-0.5 rounded border-[#30363D] bg-[#161B22] text-[#58A6FF] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-[#E6EDF3] flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#58A6FF]" />
                  <span>Enable AI triage & explanation</span>
                </span>
                <p className="text-[11px] text-[#8B949E] leading-relaxed">
                  Enriches deterministic scanner findings with structured risk assessments, prioritized fixes, and false-positive checks via Groq LLM inference.
                </p>
              </div>
            </label>

            {/* Git History Scanning Checkbox */}
            <label className="flex items-start gap-3 p-3 rounded-md bg-[#0D1117] border border-[#21262D] cursor-pointer hover:border-[#30363D] transition-colors">
              <input
                type="checkbox"
                checked={enableGitHistory}
                onChange={(e) => setEnableGitHistory(e.target.checked)}
                disabled={submitting}
                className="mt-0.5 rounded border-[#30363D] bg-[#161B22] text-[#58A6FF] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-[#E6EDF3] flex items-center gap-1.5">
                  <History className="w-3.5 h-3.5 text-[#8B949E]" />
                  <span>Scan historical Git commits</span>
                </span>
                <p className="text-[11px] text-[#8B949E] leading-relaxed">
                  Inspects recent historical commits for credentials, API tokens, or secrets that may have been committed and subsequently removed.
                </p>
              </div>
            </label>
          </div>

          {/* Preflight Note (Section 6.4) */}
          <div className="p-3.5 rounded-md bg-[#0D1117] border border-[#21262D] text-xs text-[#8B949E] space-y-1">
            <div className="flex items-center gap-1.5 text-[#E6EDF3] font-semibold text-[11px]">
              <Lock className="w-3 h-3 text-[#58A6FF]" />
              <span>Audit Execution Boundary</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Audits are processed across our deterministic engine pool (Custom AST checks, OSV vulnerability database, and Semgrep). If any mandatory engine encounters an error, the audit will be flagged as <strong>partial</strong> to prevent false claims of completeness.
            </p>
          </div>

          {/* Submission Action (Section 6.5) */}
          <div className="pt-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => router.push("/")}
              disabled={submitting}
              className="px-3 py-1.5 rounded-md text-xs font-medium text-[#8B949E] hover:text-[#E6EDF3] transition-colors"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting || !repoUrl.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold bg-[#58A6FF] hover:bg-[#79C0FF] text-[#0D1117] transition-colors shadow-xs disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[#58A6FF]/40"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Enqueuing audit...</span>
                </>
              ) : (
                <>
                  <span>Start audit</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
