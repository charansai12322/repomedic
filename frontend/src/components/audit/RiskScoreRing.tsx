"use client";

import React, { useEffect, useState, useRef } from "react";
import { SecurityScore, AuditStatus } from "@/types/repomedic";
import { getSecurityScoreColor } from "@/lib/formatters";
import { AlertTriangle, CheckCircle2, ShieldCheck, ShieldAlert } from "lucide-react";

export interface RiskScoreRingProps {
  score?: SecurityScore | null;
  partialAudit?: boolean;
  auditStatus?: AuditStatus | string;
  size?: number;
}

export function RiskScoreRing({
  score,
  partialAudit = false,
  auditStatus = "complete",
  size = 140,
}: RiskScoreRingProps) {
  const targetScore = score?.score;
  const isAvailable = targetScore !== undefined && targetScore !== null;
  const numericTarget = isAvailable ? targetScore : 0;

  const [displayedScore, setDisplayedScore] = useState<number>(0);
  const [displayedOffset, setDisplayedOffset] = useState<number>(301.59);
  const prevTargetRef = useRef<number | null>(null);

  // SVG circle calculations: R = 48 => Circumference = 2 * PI * 48 = 301.59
  const radius = 48;
  const circumference = 2 * Math.PI * radius;

  useEffect(() => {
    let animationFrameId: number;

    if (!isAvailable) {
      animationFrameId = requestAnimationFrame(() => {
        setDisplayedScore(0);
        setDisplayedOffset(circumference);
      });
      return () => {
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
      };
    }

    if (prevTargetRef.current === numericTarget) {
      // Avoid restarting on unrelated parent re-renders
      return;
    }
    prevTargetRef.current = numericTarget;

    // Check prefers-reduced-motion
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReducedMotion) {
      animationFrameId = requestAnimationFrame(() => {
        setDisplayedScore(numericTarget);
        const targetOffset = circumference - (numericTarget / 100) * circumference;
        setDisplayedOffset(targetOffset);
      });
      return () => {
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
      };
    }

    // Smooth animation curve
    const duration = 850;
    const startTime = performance.now();
    const startScore = 0;

    function animate(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Cubic ease out
      const easeProgress = 1 - Math.pow(1 - progress, 3);

      const currentScore = Math.round(startScore + (numericTarget - startScore) * easeProgress);
      const currentOffset = circumference - (currentScore / 100) * circumference;

      setDisplayedScore(currentScore);
      setDisplayedOffset(currentOffset);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      }
    }

    animationFrameId = requestAnimationFrame(animate);

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [numericTarget, isAvailable, circumference]);

  const colorMeta = getSecurityScoreColor(isAvailable ? displayedScore : 0);

  if (!isAvailable) {
    return (
      <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] flex flex-col md:flex-row items-center gap-6">
        <div className="w-28 h-28 rounded-full border-2 border-dashed border-[#30363D] flex flex-col items-center justify-center text-center p-2">
          <span className="text-xs font-semibold text-[#8B949E]">Score</span>
          <span className="text-[11px] text-[#6E7681]">Unavailable</span>
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-[#E6EDF3]">Security Score Unavailable</h3>
          <p className="text-xs text-[#8B949E] max-w-sm">
            The score could not be determined because deterministic scanner calculations remain unresolved.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-5 rounded-lg border border-[#30363D] bg-[#161B22] flex flex-col sm:flex-row items-center gap-6 shadow-sm">
      {/* Animated SVG Radial Gauge */}
      <div className="relative shrink-0 flex items-center justify-center" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox="0 0 120 120"
          className="transform -rotate-90"
          aria-hidden="true"
        >
          {/* Background Track */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="#21262D"
            strokeWidth="7"
          />
          {/* Animated Value Arc */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke={colorMeta.stroke}
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={displayedOffset}
            style={{
              transition: "stroke-dashoffset 0.05s linear",
            }}
          />
        </svg>

        {/* Center Numeric Value & Grade */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center select-none">
          <div className="flex items-baseline justify-center">
            <span className={`text-3xl font-extrabold tracking-tight font-mono ${colorMeta.text}`}>
              {displayedScore}
            </span>
            <span className="text-[10px] text-[#8B949E] font-mono ml-0.5">/100</span>
          </div>
          <div className="mt-0.5 inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-mono uppercase font-semibold bg-[#21262D] text-[#E6EDF3] border border-[#30363D]">
            Grade {score?.grade || colorMeta.grade}
          </div>
        </div>
      </div>

      {/* Score Context & Deductions */}
      <div className="space-y-3 flex-1 min-w-0 w-full sm:w-auto">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-[#E6EDF3]">Deterministic Security Score</h3>
            {partialAudit ? (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#D29922]/15 text-[#D29922] border border-[#D29922]/30">
                <AlertTriangle className="w-2.5 h-2.5" />
                Partial Coverage
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#3FB950]/15 text-[#3FB950] border border-[#3FB950]/30">
                <CheckCircle2 className="w-2.5 h-2.5" />
                Full Coverage
              </span>
            )}
          </div>
          <p className="text-xs text-[#8B949E] mt-0.5 leading-relaxed">
            {partialAudit
              ? "Calculated from completed scanners only. Required scanners encountered failures; this score does not certify complete safety."
              : "Derived from deterministic static AST analysis, custom security rules, OSV vulnerability feeds, and Semgrep."}
          </p>
        </div>

        {/* Severity Count Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[#21262D]">
          <div className="flex items-center gap-1.5 text-xs font-mono">
            <span className="text-[#8B949E]">Penalty:</span>
            <span className="text-[#E6EDF3] font-semibold">-{score?.penalty || 0} pts</span>
          </div>
          <span className="text-[#30363D]">&bull;</span>
          {score?.severity_counts && (
            <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
              <span className="text-[#F85149]">
                {score.severity_counts["critical"] || 0} Critical
              </span>
              <span className="text-[#F0883E]">
                {score.severity_counts["high"] || 0} High
              </span>
              <span className="text-[#D29922]">
                {score.severity_counts["medium"] || 0} Medium
              </span>
              <span className="text-[#58A6FF]">
                {score.severity_counts["low"] || 0} Low
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
