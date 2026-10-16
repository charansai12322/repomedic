import { NextResponse } from "next/server";

export function getBackendUrl(): string {
  return process.env.REPOMEDIC_BACKEND_URL || process.env.REPMEDIC_BACKEND_URL || "http://127.0.0.1:8000";
}

export function getBackendHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const apiKey = process.env.REPOMEDIC_API_KEY || process.env.REPMEDIC_API_KEY;
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  return headers;
}

export function handleProxyError(error: unknown) {
  const err = error as { code?: string; message?: string } | null;
  console.error("Backend proxy request failed:", err?.message || error);
  if (err?.code === "ECONNREFUSED" || err?.message?.includes("fetch failed")) {
    return NextResponse.json(
      {
        error: "BACKEND_UNAVAILABLE",
        message: "RepoMedic backend service is currently unreachable. Please ensure the Python backend server is running on port 8000.",
      },
      { status: 503 }
    );
  }
  return NextResponse.json(
    {
      error: "PROXY_ERROR",
      message: err?.message || "Internal server error occurred communicating with backend.",
    },
    { status: 500 }
  );
}
