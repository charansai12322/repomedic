"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, Activity, BarChart3, PlusCircle, CheckCircle2, AlertTriangle } from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

export function Navbar() {
  const pathname = usePathname();
  const [backendStatus, setBackendStatus] = useState<"online" | "offline" | "checking">("checking");
  const [version, setVersion] = useState<string>("");

  useEffect(() => {
    let mounted = true;
    async function check() {
      try {
        const res = await checkBackendHealth();
        if (mounted) {
          setBackendStatus(res.status === "healthy" ? "online" : "offline");
          setVersion(res.version || "2.0.0");
        }
      } catch {
        if (mounted) {
          setBackendStatus("offline");
        }
      }
    }
    check();
    const timer = setInterval(check, 15000);
    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  const navLinks = [
    { href: "/", label: "Dashboard", icon: Activity },
    { href: "/audits/new", label: "New Audit", icon: PlusCircle },
    { href: "/benchmarks", label: "Benchmarks", icon: BarChart3 },
  ];

  return (
    <nav className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-3 group">
              <div className="p-2 rounded-lg bg-blue-950/60 border border-blue-600/40 text-blue-400 group-hover:border-blue-500 transition-colors">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold text-zinc-100 tracking-tight flex items-center gap-1.5">
                  RepoMedic
                  <span className="text-[10px] uppercase font-semibold px-1.5 py-0.2 bg-zinc-800 text-zinc-400 border border-zinc-700 rounded">
                    Core v2.0
                  </span>
                </span>
                <span className="text-[11px] text-zinc-400">Security Audit Backend</span>
              </div>
            </Link>

            <div className="hidden md:flex items-center space-x-1">
              {navLinks.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-2.5 py-1 rounded-full border border-zinc-800 bg-zinc-900/80 text-xs">
              {backendStatus === "online" ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-zinc-300 font-medium">Backend Connected</span>
                  {version && <span className="text-zinc-500 text-[10px]">({version})</span>}
                </>
              ) : backendStatus === "checking" ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  <span className="text-zinc-400">Verifying API...</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-red-500" />
                  <span className="text-red-300 font-medium">Backend Offline</span>
                </>
              )}
            </div>

            <Link
              href="/audits/new"
              className="hidden sm:inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Start Audit</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
