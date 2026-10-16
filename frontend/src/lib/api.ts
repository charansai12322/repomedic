/**
 * Unified, strongly-typed API client for RepoMedic.
 * Calls Next.js BFF route handlers which proxy requests securely to the backend.
 */

import type {
  BenchmarkReport,
  BenchmarkSummary,
  DiagnosticsResponse,
  ReadinessResponse,
  ScanJob,
  ScanJobResponse,
  ScanReport,
  ScanRequestPayload,
} from "../types/repomedic.ts";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let errBody: { detail?: string; message?: string; error?: string } | null = null;
    try {
      errBody = await res.json();
    } catch {
      errBody = { detail: await res.text() };
    }
    const msg = errBody?.detail || errBody?.message || errBody?.error || `HTTP ${res.status} error`;
    throw new ApiError(msg, res.status, errBody);
  }

  return res.json() as Promise<T>;
}

export async function submitScan(payload: ScanRequestPayload): Promise<ScanJobResponse> {
  return request<ScanJobResponse>("/api/scan", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getJobStatus(jobId: string): Promise<ScanJob> {
  return request<ScanJob>(`/api/jobs/${encodeURIComponent(jobId)}`);
}

export async function getJobReport(jobId: string): Promise<ScanReport> {
  return request<ScanReport>(`/api/jobs/${encodeURIComponent(jobId)}/report`);
}

export async function listRecentJobs(limit: number = 20): Promise<ScanJob[]> {
  return request<ScanJob[]>(`/api/jobs?limit=${limit}`);
}

export async function cancelJob(jobId: string): Promise<ScanJob> {
  return request<ScanJob>(`/api/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: "POST",
  });
}

export async function getBenchmarkSummary(): Promise<BenchmarkSummary> {
  return request<BenchmarkSummary>("/api/benchmarks/summary");
}

export async function getLatestBenchmark(): Promise<BenchmarkReport> {
  return request<BenchmarkReport>("/api/benchmarks/latest");
}

export async function checkBackendHealth(): Promise<{ status: string; version: string }> {
  return request<{ status: string; version: string }>("/api/health");
}

export async function checkBackendReadiness(): Promise<ReadinessResponse> {
  return request<ReadinessResponse>("/api/ready");
}

export async function getDiagnostics(): Promise<DiagnosticsResponse> {
  return request<DiagnosticsResponse>("/api/diagnostics");
}
