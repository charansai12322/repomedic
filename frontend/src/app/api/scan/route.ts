import { NextRequest, NextResponse } from "next/server";
import { getBackendHeaders, getBackendUrl, handleProxyError } from "@/lib/server-proxy";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const backendUrl = getBackendUrl();
    const headers = getBackendHeaders();

    const backendRes = await fetch(`${backendUrl}/scan`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    const data = await backendRes.json();
    return NextResponse.json(data, { status: backendRes.status });
  } catch (err) {
    return handleProxyError(err);
  }
}
