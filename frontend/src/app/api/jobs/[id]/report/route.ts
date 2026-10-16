import { NextRequest, NextResponse } from "next/server";
import { getBackendHeaders, getBackendUrl, handleProxyError } from "@/lib/server-proxy";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const format = req.nextUrl.searchParams.get("format") || "json";
    const backendUrl = getBackendUrl();
    const headers = getBackendHeaders();

    const backendRes = await fetch(
      `${backendUrl}/jobs/${encodeURIComponent(id)}/report?format=${encodeURIComponent(format)}`,
      {
        method: "GET",
        headers,
        cache: "no-store",
      }
    );

    if (!backendRes.ok) {
      const errText = await backendRes.text();
      return new NextResponse(errText, {
        status: backendRes.status,
        headers: { "Content-Type": "application/json" },
      });
    }

    const contentType = backendRes.headers.get("content-type") || "application/json";
    const contentDisposition = backendRes.headers.get("content-disposition") || "";
    const body = await backendRes.text();

    const responseHeaders: Record<string, string> = {
      "Content-Type": contentType,
    };
    if (contentDisposition) {
      responseHeaders["Content-Disposition"] = contentDisposition;
    }

    return new NextResponse(body, {
      status: 200,
      headers: responseHeaders,
    });
  } catch (err) {
    return handleProxyError(err);
  }
}
