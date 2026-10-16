"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PlusCircle,
  History,
  BarChart3,
  Activity,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  ShieldCheck,
  Radio,
  Lock,
} from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"online" | "offline" | "checking">("checking");
  const [version, setVersion] = useState<string>("");
  const [environment, setEnvironment] = useState<string>("");

  useEffect(() => {
    let mounted = true;
    async function check() {
      try {
        const res = await checkBackendHealth();
        if (mounted) {
          setBackendStatus(res.status === "ok" || res.status === "healthy" ? "online" : "offline");
          setVersion(res.version || "2.0.0");
          const healthData = res as Record<string, unknown>;
          if (typeof healthData.environment === "string") {
            setEnvironment(healthData.environment);
          }
        }
      } catch {
        if (mounted) {
          setBackendStatus("offline");
        }
      }
    }

    check();
    const interval = setInterval(check, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const [prevPathname, setPrevPathname] = useState(pathname);
  if (prevPathname !== pathname) {
    setPrevPathname(pathname);
    setMobileOpen(false);
  }

  const navItems = [
    { href: "/", label: "Overview", icon: LayoutDashboard, exact: true },
    { href: "/audits/new", label: "New Audit", icon: PlusCircle, exact: false },
    { href: "/#recent-audits", label: "Audit History", icon: History, exact: false, isHash: true },
    { href: "/benchmarks", label: "Benchmarks", icon: BarChart3, exact: false },
    { href: "/diagnostics", label: "Scanner Health", icon: Activity, exact: false },
  ];

  return (
    <div className="min-h-screen bg-[#0D1117] text-[#E6EDF3] flex flex-col md:flex-row antialiased">
      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-[#010409] border-b border-[#30363D] sticky top-0 z-40">
        <Link href="/" className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded bg-[#161B22] border border-[#30363D] flex items-center justify-center text-[#58A6FF]">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <circle cx="12" cy="11" r="3" />
            </svg>
          </div>
          <div>
            <span className="text-sm font-semibold text-[#E6EDF3] tracking-tight">RepoMedic</span>
            <span className="text-[10px] text-[#8B949E] block -mt-0.5">Security Workbench</span>
          </div>
        </Link>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-[#161B22] border border-[#30363D] text-[10px]">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                backendStatus === "online"
                  ? "bg-[#3FB950]"
                  : backendStatus === "checking"
                  ? "bg-[#D29922]"
                  : "bg-[#F85149]"
              }`}
            />
            <span className="text-[#8B949E]">
              {backendStatus === "online" ? "API Live" : backendStatus === "checking" ? "Checking" : "Offline"}
            </span>
          </div>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-1.5 rounded text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22] focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/70 backdrop-blur-xs z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Navigation Rail */}
      <aside
        className={`fixed md:sticky top-0 bottom-0 left-0 z-50 md:z-30 h-screen bg-[#010409] border-r border-[#30363D] flex flex-col justify-between transition-all duration-200 select-none ${
          mobileOpen ? "translate-x-0 w-64" : "-translate-x-full md:translate-x-0"
        } ${collapsed ? "md:w-16" : "md:w-56"}`}
        aria-label="Main Navigation"
      >
        {/* Top Header & Brand */}
        <div>
          <div className="h-14 flex items-center justify-between px-3.5 border-b border-[#21262D]">
            <Link
              href="/"
              className={`flex items-center gap-2.5 overflow-hidden transition-opacity ${
                collapsed ? "justify-center w-full" : ""
              }`}
              title="RepoMedic — Developer Security Workbench"
            >
              <div className="w-7 h-7 rounded bg-[#161B22] border border-[#30363D] flex items-center justify-center text-[#58A6FF] shrink-0">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <circle cx="12" cy="11" r="3" />
                </svg>
              </div>
              {!collapsed && (
                <div className="flex flex-col truncate">
                  <span className="text-xs font-semibold text-[#E6EDF3] tracking-tight flex items-center gap-1.5">
                    RepoMedic
                    <span className="text-[9px] uppercase font-mono px-1 py-0.2 bg-[#161B22] text-[#8B949E] border border-[#30363D] rounded">
                      v2
                    </span>
                  </span>
                  <span className="text-[10px] text-[#8B949E] truncate">Repository Security</span>
                </div>
              )}
            </Link>

            {!collapsed && (
              <button
                onClick={() => setCollapsed(true)}
                className="hidden md:flex p-1 rounded hover:bg-[#161B22] text-[#8B949E] hover:text-[#E6EDF3] transition-colors"
                title="Collapse sidebar"
                aria-label="Collapse sidebar"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Nav Links */}
          <nav className="p-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.isHash
                ? false
                : item.exact
                ? pathname === item.href
                : pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={collapsed ? item.label : undefined}
                  className={`group flex items-center gap-2.5 px-2.5 py-2 rounded-md text-xs font-medium transition-colors relative ${
                    isActive
                      ? "bg-[#161B22] text-[#E6EDF3] font-semibold"
                      : "text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#161B22]/70"
                  } ${collapsed ? "justify-center" : ""}`}
                >
                  {/* Left accent bar for active link */}
                  {isActive && (
                    <span
                      className="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-[#58A6FF] rounded-r"
                      aria-hidden="true"
                    />
                  )}
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      isActive ? "text-[#58A6FF]" : "text-[#8B949E] group-hover:text-[#E6EDF3]"
                    }`}
                  />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Bottom Section: Expand Button, Backend Health, Boundary Guarantee */}
        <div className="p-3 border-t border-[#21262D] space-y-3">
          {collapsed && (
            <div className="flex justify-center pb-1">
              <button
                onClick={() => setCollapsed(false)}
                className="hidden md:flex p-1.5 rounded hover:bg-[#161B22] text-[#8B949E] hover:text-[#E6EDF3] transition-colors"
                title="Expand sidebar"
                aria-label="Expand sidebar"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Backend Status Card */}
          <div
            className={`rounded border border-[#30363D] bg-[#161B22]/60 p-2 text-[11px] ${
              collapsed ? "flex justify-center" : "space-y-1"
            }`}
            title={`Backend: ${backendStatus} | Version: ${version || "2.0.0"}`}
          >
            {collapsed ? (
              <span
                className={`w-2 h-2 rounded-full ${
                  backendStatus === "online"
                    ? "bg-[#3FB950]"
                    : backendStatus === "checking"
                    ? "bg-[#D29922]"
                    : "bg-[#F85149]"
                }`}
              />
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        backendStatus === "online"
                          ? "bg-[#3FB950]"
                          : backendStatus === "checking"
                          ? "bg-[#D29922]"
                          : "bg-[#F85149]"
                      }`}
                    />
                    <span className="font-semibold text-[#E6EDF3]">
                      {backendStatus === "online"
                        ? "Engine Online"
                        : backendStatus === "checking"
                        ? "Verifying..."
                        : "Engine Offline"}
                    </span>
                  </div>
                  {version && (
                    <span className="font-mono text-[9px] text-[#8B949E]">v{version}</span>
                  )}
                </div>
                <div className="text-[10px] text-[#8B949E] flex items-center justify-between">
                  <span>FastAPI Service</span>
                  <span className="font-mono text-[9px] text-[#8B949E]">
                    {environment || "local"}
                  </span>
                </div>
              </>
            )}
          </div>

          {!collapsed && (
            <div className="px-1 text-[10px] text-[#6E7681] leading-tight flex items-start gap-1.5">
              <Lock className="w-3 h-3 text-[#8B949E] shrink-0 mt-0.5" />
              <span>Static analysis only. Target code is never executed.</span>
            </div>
          )}
        </div>
      </aside>

      {/* Main Workbench Viewport */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {children}
        </main>

        {/* Minimal Footer */}
        <footer className="border-t border-[#21262D] bg-[#010409] py-4 text-xs text-[#8B949E]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px]">
            <div className="flex items-center space-x-3">
              <span className="font-semibold text-[#E6EDF3]">RepoMedic Security Platform</span>
              <span>&bull;</span>
              <span>SARIF 2.1.0 Compatible</span>
              <span>&bull;</span>
              <span>OSV Vulnerability DB</span>
            </div>
            <div className="font-mono text-[#6E7681]">
              Zero-Trust Redaction &bull; Deterministic Core
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
