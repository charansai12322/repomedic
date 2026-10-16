import { NextRequest, NextResponse } from "next/server";
import { getBackendHeaders, getBackendUrl, handleProxyError } from "@/lib/server-proxy";

export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const limit = searchParams.get("limit") || "20";
    const backendUrl = getBackendUrl();
    const headers = getBackendHeaders();

    const backendRes = await fetch(`${backendUrl}/jobs?limit=${limit}`, {
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
