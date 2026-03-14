import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function DashboardOverviewPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mb-10">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Overview
        </h1>
        <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">
          Start a new email campaign or leverage existing campaign data.
        </p>
      </div>

      <div className="space-y-12">
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            New email campaign
          </h2>
          <div className="mt-4 grid gap-5 sm:grid-cols-2">
            <Card className="border-zinc-200 dark:border-zinc-700">
              <CardHeader>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Connect your store
                </h3>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  Link your Shopify store once. We sync customers and orders so you can target the right people.
                </p>
                <Button asChild className="mt-4">
                  <Link href="/dashboard/connect">Connect store</Link>
                </Button>
              </CardContent>
            </Card>
            <Card className="border-zinc-200 dark:border-zinc-700">
              <CardHeader>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Create a campaign
                </h3>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  Set subject, audience, and send or schedule. Optionally use insights from past campaigns.
                </p>
                <Button asChild variant="outline" className="mt-4">
                  <Link href="/dashboard/recommendations">Create campaign</Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Leverage existing campaigns
          </h2>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            Upload past data, search it, run experiments, and generate new campaigns from what works.
          </p>
          <Button asChild variant="outline" className="mt-4">
            <Link href="/dashboard/leverage">Open leverage hub</Link>
          </Button>
          <ul className="mt-4 flex flex-wrap gap-2">
            {[
              { label: "Data upload", href: "/dashboard/data-upload" },
              { label: "SQL Explorer", href: "/dashboard/sql-explorer" },
              { label: "Campaign strategy", href: "/dashboard/campaign-strategy" },
              { label: "Recommendations", href: "/dashboard/recommendations" },
              { label: "Inventory", href: "/dashboard/inventory" },
            ].map(({ label, href }) => (
              <li key={href}>
                <Link
                  href={href}
                  className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 hover:border-zinc-300 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
                >
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
