/**
 * Canonical TypeScript types for RepoMedic frontend matching backend Pydantic models.
 */

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type Confidence = "high" | "medium" | "low";

export type EvidenceQuality = "deterministic" | "ai_interpretation" | "unverified";

export type ScannerStatus = "completed" | "failed" | "unavailable" | "skipped" | "running";

export type AuditStatus = "complete" | "partial" | "failed";

export type JobState = "queued" | "running" | "completed" | "partial" | "failed";

export interface Finding {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  confidence: Confidence;
  source: string;
  evidence_quality: EvidenceQuality;
  rule_id: string;
  file_path: string;
  line_start: number;
  line_end: number;
  evidence: string;
  remediation: string;
  references: string[];
  corroborating_sources?: string[];
  fingerprint?: string | null;
}

export interface ScannerHealth {
  status: ScannerStatus;
  required: boolean;
  duration_ms: number;
  error_code?: string | null;
  error_message?: string | null;
  finding_count: number;
}

export interface ScanHealthSummary {
  scanners: Record<string, ScannerHealth>;
  audit_status: AuditStatus;
  partial_audit: boolean;
  start_time: string;
  finish_time: string;
  total_duration_ms: number;
  degraded_reasons: string[];
}

export interface SecurityScore {
  score: number;
  grade: "A" | "B" | "C" | "D" | "F";
  penalty: number;
  severity_counts: Record<string, number>;
}

export interface ScanEvidenceSummary {
  files_scanned: number;
  scan_truncated: boolean;
  large_files_skipped: number;
  findings: Finding[];
}

export interface AIDiagnosis {
  finding_id: string;
  title: string;
  why_it_matters: string;
  fix: string;
  priority: number;
  likely_false_positive: boolean;
}

export interface AITriageResult {
  executive_summary: string;
  diagnoses: AIDiagnosis[];
  limitations: string[];
  citation_validity_percent: number;
  model: string;
  mode: "groq" | "deterministic_only";
  duration_ms: number;
}

export interface ScanReport {
  target: string;
  scan_health: ScanHealthSummary;
  score: SecurityScore;
  evidence: ScanEvidenceSummary;
  ai_triage: AITriageResult;
  security_boundary: string;
  partial_audit: boolean;
  audit_status: AuditStatus;
}

export interface ScanJob {
  job_id: string;
  target: string;
  state: JobState;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  progress_percent: number;
  current_step: string;
  error?: string | null;
  report?: ScanReport | null;
}

export interface ScanJobResponse {
  job_id: string;
  status: JobState;
  message: string;
}

export interface ScanRequestPayload {
  repo_url: string;
  enable_git_history?: boolean;
  enable_ai?: boolean;
  max_history_commits?: number;
}

export interface ReadinessResponse {
  status: string;
  service: string;
  version: string;
  scanners: Record<string, string>;
  ai_inference: {
    mode: "groq" | "deterministic_only";
    configured: boolean;
  };
}

export interface DiagnosticsResponse {
  service: string;
  version: string;
  environment: string;
  tools: {
    semgrep_installed: boolean;
    git_installed: boolean;
  };
  ai_discovery: {
    cached_model_count: number;
    active_model: string;
    configured_override: string | null;
    preferences: string[];
    cache_age_seconds: number | null;
  };
  limits: {
    max_concurrent_scans: number;
    max_queue_capacity: number;
    scan_timeout_seconds: number;
    max_repo_mb: number;
    max_repo_files: number;
  };
  scanner_policies: {
    semgrep_required: boolean;
    osv_required: boolean;
    custom_rules_required: boolean;
    python_ast_required: boolean;
    ai_triage_required: boolean;
  };
}

export interface FixtureEvaluation {
  fixture_id: string;
  name: string;
  is_negative_control: boolean;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
  duration_ms: number;
  audit_status: string;
  partial_audit: boolean;
}

export interface BenchmarkReport {
  timestamp_utc: string;
  total_fixtures: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  true_negatives: number;
  precision: number | null;
  recall: number | null;
  false_positive_rate: number | null;
  f1_score: number | null;
  ai_citation_validity: number;
  average_scan_duration_ms: number;
  median_scan_duration_ms: number;
  scanner_availability_rate: number;
  scanner_failure_rate: number;
  partial_audit_rate: number;
  evaluations: FixtureEvaluation[];
}

export interface BenchmarkSummary {
  timestamp_utc: string;
  total_fixtures: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  true_negatives: number;
  precision: number;
  recall: number;
  false_positive_rate: number;
  f1_score: number;
  ai_citation_validity: number;
  average_scan_duration_ms: number;
  median_scan_duration_ms: number;
  scanner_availability_rate: number;
  scanner_failure_rate: number;
  partial_audit_rate: number;
}
