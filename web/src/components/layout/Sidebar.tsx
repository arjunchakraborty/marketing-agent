"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

interface NavItem {
  label: string;
  href: string;
  icon: string;
  badge?: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const navigation: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { label: "Home", href: "/", icon: "🏠" },
      { label: "Dashboard", href: "/dashboard", icon: "📊" },
    ],
  },
  {
    label: "Campaigns",
    items: [
      { label: "Create Campaign", href: "/campaigns/target", icon: "🎯" },
      { label: "Campaign Demo", href: "/campaigns/demo", icon: "✨" },
      { label: "Campaign Images", href: "/campaigns/images", icon: "🖼️" },
      { label: "Email Preview", href: "/campaigns/email-preview", icon: "📧" },
    ],
  },
  {
    label: "Workflow",
    items: [
      { label: "Workflow Guide", href: "/workflow", icon: "🔄" },
      { label: "Workflow Demo", href: "/workflow/demo", icon: "🎬" },
      { label: "Upload Data", href: "/upload", icon: "📤" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 min-h-[44px] min-w-[44px] p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-lg"
        aria-label="Toggle menu"
      >
        <svg
          className="w-6 h-6 text-slate-600 dark:text-slate-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {mobileOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 z-40
          transform transition-transform duration-300 ease-in-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
          lg:translate-x-0
          overflow-y-auto
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo/Header */}
          <div className="p-4 md:p-6 border-b border-slate-200 dark:border-slate-700">
            <div className="mb-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Marketing Intelligence
              </p>
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                Control Center
              </h1>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-2 hidden lg:block">
              Unified analytics and campaign orchestration
            </p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-6 overflow-y-auto">
            {navigation.map((group) => (
              <div key={group.label}>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-2 px-3">
                  {group.label}
                </h3>
                <ul className="space-y-1">
                  {group.items.map((item) => {
                    const active = isActive(item.href);
                    return (
                      <li key={item.href}>
                        <Link
                          href={item.href}
                          onClick={() => setMobileOpen(false)}
                          className={`
                            flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                            ${
                              active
                                ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-l-4 border-blue-600"
                                : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                            }
                          `}
                        >
                          <span className="text-lg">{item.icon}</span>
                          <span className="flex-1">{item.label}</span>
                          {item.badge && (
                            <span className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                              {item.badge}
                            </span>
                          )}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>

          {/* Footer Actions */}
          <div className="p-4 border-t border-slate-200 dark:border-slate-700 space-y-2">
            <Link
              href="/campaigns/target"
              className="flex items-center justify-center gap-2 w-full min-h-[44px] px-4 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-lg font-medium hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors text-sm"
            >
              <span>🚀</span>
              <span>Launch Campaign</span>
            </Link>
            <div className="flex items-center justify-center">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

