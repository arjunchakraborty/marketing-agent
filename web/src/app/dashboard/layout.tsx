import { DashboardNav } from "@/components/layout/DashboardNav";
import { DashboardHealthBanner } from "@/components/dashboard/DashboardHealthBanner";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <DashboardNav />
      <div className="flex flex-1 flex-col overflow-auto">
        <DashboardHealthBanner />
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
