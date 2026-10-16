import { NextRequest, NextResponse } from "next/server";
import { getBackendHeaders, getBackendUrl, handleProxyError } from "@/lib/server-proxy";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const backendUrl = getBackendUrl();
    const headers = getBackendHeaders();

    const backendRes = await fetch(`${backendUrl}/jobs/${encodeURIComponent(id)}`, {
      method: "GET",
      headers,
      cache: "no-store",
    });

    const data = await backendRes.json();
    return NextResponse.json(data, { status: backendRes.status });
  } catch (err) {
    return handleProxyError(err);
  }
}
