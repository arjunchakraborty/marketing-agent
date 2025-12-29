"use client";

import { ReactNode, useState } from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

interface AppShellProps {
  children: ReactNode;
}

const navigation = [
  { label: "Home", href: "/" },
  { label: "Dashboard", href: "/dashboard" },
  { label: "Workflow", href: "/workflow" },
  { label: "Upload", href: "/upload" },
  { label: "Campaign Images", href: "/campaigns/images" },
  { label: "Email Preview", href: "/campaigns/email-preview" },
  { label: "Target Campaign", href: "/campaigns/target" },
  { label: "Campaign Demo", href: "/campaigns/demo" },
];

export function AppShell({ children }: AppShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-slate-200 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-700 dark:bg-slate-800/80 sticky top-0 z-50">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 md:px-6 py-4 md:py-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Marketing Intelligence</p>
              <h1 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100">Marketing Control Center</h1>
              <p className="text-xs md:text-sm text-slate-600 dark:text-slate-300 hidden sm:block">
                Unified analytics, ingestion, and campaign orchestration powered by the agent workflow stack.
              </p>
            </div>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="sm:hidden min-h-[44px] min-w-[44px] p-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700"
              aria-label="Toggle menu"
            >
              <svg
                className="w-6 h-6 text-slate-600 dark:text-slate-300"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                {mobileMenuOpen ? (
                  <path d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
          <div className={`flex flex-col sm:flex-row items-stretch sm:items-center gap-2 ${mobileMenuOpen ? "block" : "hidden sm:flex"}`}>
            <Link
              href="/dashboard"
              className="min-h-[44px] px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 rounded-full border border-slate-200 dark:border-slate-700 transition-colors hover:border-slate-300 hover:text-slate-800 dark:hover:border-slate-600 dark:hover:text-slate-100 text-center"
            >
              Daily Digest
            </Link>
            <Link
              href="/campaigns/target"
              className="min-h-[44px] px-4 py-2 text-sm font-medium text-white dark:text-slate-900 rounded-full bg-slate-900 dark:bg-slate-100 shadow-sm transition-colors hover:bg-slate-700 dark:hover:bg-slate-200 text-center"
            >
              Launch Automation
            </Link>
            <div className="flex justify-center sm:justify-start">
              <ThemeToggle />
            </div>
          </div>
        </div>
        <nav className={`border-t border-slate-100 dark:border-slate-700 ${mobileMenuOpen ? "block" : "hidden sm:block"}`}>
          <div className="mx-auto flex max-w-7xl flex-col sm:flex-row gap-2 sm:gap-4 overflow-x-auto px-4 md:px-6 py-3 text-sm text-slate-600 dark:text-slate-300">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="min-h-[44px] rounded-full border border-transparent px-4 py-2 font-medium transition-colors hover:border-slate-300 hover:bg-white hover:text-slate-900 dark:hover:border-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-100 text-center"
                onClick={() => setMobileMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-4 md:px-6 py-6 md:py-10">
        {children}
      </main>
    </div>
  );
}
