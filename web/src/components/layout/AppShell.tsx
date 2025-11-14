import { ReactNode } from "react";

interface AppShellProps {
  children: ReactNode;
}

const navigation = [
  { label: "Overview", href: "#overview" },
  { label: "SQL Explorer", href: "#sql-explorer" },
  { label: "Experiment Planner", href: "#experiments" },
  { label: "Campaign Strategy", href: "#campaign-strategy-experiment" },
  { label: "Campaigns", href: "#campaigns" },
  { label: "Inventory", href: "#inventory" },
];

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-slate-200">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Marketing Intelligence</p>
            <h1 className="text-2xl font-semibold text-slate-900">TripleWhale Inspired Control Center</h1>
            <p className="text-sm text-slate-600">
              Unified analytics, ingestion, and campaign orchestration powered by the agent workflow stack.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:border-slate-300 hover:text-slate-800">
              Daily Digest
            </button>
            <button className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-700">
              Launch Automation
            </button>
          </div>
        </div>
        <nav className="border-t border-slate-100">
          <div className="mx-auto flex max-w-7xl gap-4 overflow-x-auto px-6 py-3 text-sm text-slate-600">
            {navigation.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="rounded-full border border-transparent px-4 py-2 font-medium transition hover:border-slate-300 hover:bg-white hover:text-slate-900"
              >
                {item.label}
              </a>
            ))}
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-10">
        {children}
      </main>
    </div>
  );
}
