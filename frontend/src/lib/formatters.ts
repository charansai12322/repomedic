/**
 * Data formatters and presentation helpers for RepoMedic frontend.
 */

export function formatDuration(seconds?: number): string {
  if (seconds === undefined || seconds === null) return "N/A";
  if (seconds < 1) return `${seconds.toFixed(2)}s`;
  if (seconds < 60) return `${seconds.toFixed(2)}s`;
  const mins = Math.floor(seconds / 60);
  const remainingSecs = Math.round(seconds % 60);
  return `${mins}m ${remainingSecs}s`;
}

export function formatDurationMs(ms?: number): string {
  if (ms === undefined || ms === null) return "N/A";
  if (ms < 1000) return `${ms}ms`;
  return formatDuration(ms / 1000);
}

export function getSeverityBadgeClass(severity: string): string {
  switch (severity?.toLowerCase()) {
    case "critical":
      return "bg-red-500/10 text-red-400 border-red-500/30";
    case "high":
      return "bg-orange-500/10 text-orange-400 border-orange-500/30";
    case "medium":
      return "bg-amber-500/10 text-amber-400 border-amber-500/30";
    case "low":
      return "bg-blue-500/10 text-blue-400 border-blue-500/30";
    case "info":
    default:
      return "bg-slate-500/10 text-slate-400 border-slate-500/30";
  }
}

/**
 * Risk penalty color (higher penalty = redder)
 */
export function getRiskColor(score: number): string {
  if (score >= 80) return "text-red-400";
  if (score >= 60) return "text-orange-400";
  if (score >= 40) return "text-amber-400";
  if (score >= 20) return "text-blue-400";
  return "text-emerald-400";
}

/**
 * Security score color (100 = best/green, 0 = worst/red)
 */
export function getSecurityScoreColor(score: number): {
  text: string;
  stroke: string;
  bg: string;
  grade: string;
} {
  if (score >= 85) {
    return {
      text: "text-emerald-400",
      stroke: "#3FB950",
      bg: "bg-emerald-950/20 border-emerald-500/30",
      grade: "A",
    };
  }
  if (score >= 70) {
    return {
      text: "text-blue-400",
      stroke: "#58A6FF",
      bg: "bg-blue-950/20 border-blue-500/30",
      grade: "B",
    };
  }
  if (score >= 55) {
    return {
      text: "text-amber-400",
      stroke: "#D29922",
      bg: "bg-amber-950/20 border-amber-500/30",
      grade: "C",
    };
  }
  if (score >= 40) {
    return {
      text: "text-orange-400",
      stroke: "#F0883E",
      bg: "bg-orange-950/20 border-orange-500/30",
      grade: "D",
    };
  }
  return {
    text: "text-red-400",
    stroke: "#F85149",
    bg: "bg-red-950/20 border-red-500/30",
    grade: "F",
  };
}

export function validateGitRepoUrl(url: string): { valid: boolean; error?: string } {
  const trimmed = url.trim();
  if (!trimmed) {
    return { valid: false, error: "Repository URL cannot be empty." };
  }

  // Reject local file paths and internal metadata
  const lower = trimmed.toLowerCase();
  if (
    lower.includes("127.0.0.1") ||
    lower.includes("localhost") ||
    lower.includes("169.254.169.254") ||
    lower.startsWith("file://")
  ) {
    return { valid: false, error: "Localhost and metadata IP targets are prohibited." };
  }

  // Supported: https://github.com/org/repo or git@github.com:...
  const httpsPattern = /^https?:\/\/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(\/[a-zA-Z0-9_.-]+)+\/?$/;
  const sshPattern = /^git@[a-zA-Z0-9.-]+:[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+(\.git)?$/;

  if (!httpsPattern.test(trimmed) && !sshPattern.test(trimmed)) {
    return { valid: false, error: "Invalid Git repository URL format. Please provide a valid HTTPS or SSH URL." };
  }

  return { valid: true };
}

export function redactSensitiveString(text: string): string {
  if (!text) return "";
  // Redact common credential patterns (OpenAI, AWS, GitHub tokens, generic hex tokens)
  return text
    .replace(/(ghp_[a-zA-Z0-9]{36})/g, "ghp_************************************")
    .replace(/(AKIA[0-9A-Z]{16})/g, "AKIA****************")
    .replace(/(sk-[a-zA-Z0-9-_]{20,})/g, "sk-********************");
}

export function formatRelativeTimestamp(isoDateStr?: string | null): string {
  if (!isoDateStr) return "N/A";
  try {
    const date = new Date(isoDateStr);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSec < 60) return "just now";
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return isoDateStr;
  }
}
