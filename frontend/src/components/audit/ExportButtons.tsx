"use client";

import React, { useState, useRef, useEffect } from "react";
import { Download, FileCode, FileText, ChevronDown, Loader2, AlertCircle } from "lucide-react";

interface ExportButtonsProps {
  jobId: string;
}

export function ExportButtons({ jobId }: ExportButtonsProps) {
  const [open, setOpen] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleDownload(format: "sarif" | "json" | "html") {
    setExportError(null);
    try {
      setDownloading(format);
      const url = `/api/jobs/${encodeURIComponent(jobId)}/report?format=${format}`;
      const res = await fetch(url);
      if (!res.ok) {
        let errMsg = `Export request failed with status ${res.status}`;
        try {
          const errData = await res.json();
          if (errData?.detail) errMsg = errData.detail;
        } catch {
          // fallback
        }
        throw new Error(errMsg);
      }

      const blob = await res.blob();
      const ext = format === "sarif" ? "sarif" : format === "json" ? "json" : "html";
      const filename = `repomedic-audit-${jobId.slice(0, 8)}.${ext}`;

      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
      setOpen(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to download report.";
      setExportError(msg);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      <div className="flex items-center gap-1.5">
        {exportError && (
          <span className="text-[11px] text-[#F85149] flex items-center gap-1 mr-2" role="alert">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>{exportError}</span>
          </span>
        )}

        <button
          onClick={() => setOpen(!open)}
          disabled={downloading !== null}
          aria-expanded={open}
          aria-haspopup="true"
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold bg-[#21262D] hover:bg-[#30363D] text-[#E6EDF3] border border-[#30363D] transition-colors disabled:opacity-50 focus:outline-none focus:ring-1 focus:ring-[#58A6FF]"
        >
          {downloading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-[#58A6FF]" />
          ) : (
            <Download className="w-3.5 h-3.5 text-[#58A6FF]" />
          )}
          <span>{downloading ? `Exporting ${downloading.toUpperCase()}...` : "Export Report"}</span>
          <ChevronDown className="w-3.5 h-3.5 text-[#8B949E]" />
        </button>
      </div>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-1.5 w-60 rounded-md bg-[#161B22] border border-[#30363D] shadow-xl py-1 z-30 focus:outline-none"
        >
          <div className="px-3 py-1.5 border-b border-[#21262D]">
            <span className="text-[10px] uppercase font-mono tracking-wider text-[#8B949E] font-semibold">
              Select Export Format
            </span>
          </div>

          <button
            role="menuitem"
            onClick={() => handleDownload("sarif")}
            disabled={downloading !== null}
            className="w-full text-left px-3 py-2 text-xs flex items-center justify-between text-[#E6EDF3] hover:bg-[#21262D] transition-colors"
          >
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-[#58A6FF]" />
              <div>
                <span className="font-semibold block">OASIS SARIF 2.1.0</span>
                <span className="text-[10px] text-[#8B949E] block">For GitHub Code Scanning & CI</span>
              </div>
            </div>
            {downloading === "sarif" && <Loader2 className="w-3 h-3 animate-spin text-[#58A6FF]" />}
          </button>

          <button
            role="menuitem"
            onClick={() => handleDownload("json")}
            disabled={downloading !== null}
            className="w-full text-left px-3 py-2 text-xs flex items-center justify-between text-[#E6EDF3] hover:bg-[#21262D] transition-colors"
          >
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4 text-[#D29922]" />
              <div>
                <span className="font-semibold block">Canonical JSON</span>
                <span className="text-[10px] text-[#8B949E] block">Full raw findings & health schema</span>
              </div>
            </div>
            {downloading === "json" && <Loader2 className="w-3 h-3 animate-spin text-[#D29922]" />}
          </button>

          <button
            role="menuitem"
            onClick={() => handleDownload("html")}
            disabled={downloading !== null}
            className="w-full text-left px-3 py-2 text-xs flex items-center justify-between text-[#E6EDF3] hover:bg-[#21262D] transition-colors"
          >
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#3FB950]" />
              <div>
                <span className="font-semibold block">Standalone HTML</span>
                <span className="text-[10px] text-[#8B949E] block">Self-contained browser report</span>
              </div>
            </div>
            {downloading === "html" && <Loader2 className="w-3 h-3 animate-spin text-[#3FB950]" />}
          </button>
        </div>
      )}
    </div>
  );
}
