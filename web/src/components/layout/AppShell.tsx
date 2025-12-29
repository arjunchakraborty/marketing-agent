"use client";

import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-slate-200 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors">
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="lg:pl-64">
        <main className="px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
          <div className="w-full max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
