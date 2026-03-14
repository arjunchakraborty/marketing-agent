"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

const newCampaignItems = [
  { label: "Overview", href: "/dashboard" },
  { label: "Connect store", href: "/dashboard/connect" },
  { label: "Campaigns", href: "/dashboard/campaigns" },
  { label: "Create campaign", href: "/dashboard/recommendations?mode=new" },
];

const leverageItems = [
  { label: "Leverage hub", href: "/dashboard/leverage" },
  { label: "Data upload", href: "/dashboard/data-upload" },
  { label: "SQL Explorer", href: "/dashboard/sql-explorer" },
  { label: "Campaign strategy", href: "/dashboard/campaign-strategy" },
  { label: "Recommendations", href: "/dashboard/recommendations" },
  { label: "Inventory", href: "/dashboard/inventory" },
];

function NavSection({
  title,
  items,
  pathname,
}: {
  title: string;
  items: { label: string; href: string }[];
  pathname: string;
}) {
  return (
    <div className="mb-6">
      <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
        {title}
      </p>
      <div className="space-y-0.5">
        {items.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-violet-100 text-violet-800 dark:bg-violet-900/50 dark:text-violet-200"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 flex-col border-r border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex h-14 items-center justify-between border-b border-zinc-200 px-4 dark:border-zinc-800">
        <Link
          href="/"
          className="text-sm font-semibold text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-white"
        >
          ← Home
        </Link>
        <ThemeToggle />
      </div>
      <nav className="flex-1 overflow-y-auto p-3">
        <NavSection
          title="New email campaign"
          items={newCampaignItems}
          pathname={pathname}
        />
        <NavSection
          title="Leverage existing"
          items={leverageItems}
          pathname={pathname}
        />
      </nav>
    </aside>
  );
}
