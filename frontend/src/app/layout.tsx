import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RepoMedic — Security Workbench for Repository Auditing",
  description:
    "Deterministic multi-scanner security analysis with AI triage, scanner health guarantees, and zero-compromise secret redaction.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full dark`}
    >
      <body className="min-h-full bg-[#0D1117] text-[#E6EDF3] font-sans antialiased selection:bg-[#58A6FF]/30 selection:text-white">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
