import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const tools = [
  {
    title: "Data upload",
    href: "/dashboard/data-upload",
    description: "Upload past campaign and product data (zip). Ingest CSV and image analyses into the vector DB for search and strategy.",
  },
  {
    title: "SQL Explorer",
    href: "/dashboard/sql-explorer",
    description: "Search campaigns with natural language. Find what performed well and reuse patterns for new campaigns.",
  },
  {
    title: "Campaign strategy",
    href: "/dashboard/campaign-strategy",
    description: "Run experiments on past campaigns. Analyze visuals, correlate with performance, and get hero image and content prompts.",
  },
  {
    title: "Recommendations",
    href: "/dashboard/recommendations",
    description: "Campaign recommendations and planning. Generate new campaigns from experiment insights.",
  },
  {
    title: "Inventory",
    href: "/dashboard/inventory",
    description: "Inventory alerts and low-stock items. Use product context when generating campaigns.",
  },
];

export default function LeverageHubPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Leverage existing campaigns
        </h1>
        <p className="mt-1.5 max-w-2xl text-zinc-600 dark:text-zinc-400">
          Ingest past data, explore with SQL, run strategy experiments, and generate new email campaigns from what already works.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {tools.map((tool) => (
          <Link key={tool.href} href={tool.href}>
            <Card className="h-full transition-shadow hover:shadow-md border-zinc-200 dark:border-zinc-700 hover:border-violet-200 dark:hover:border-violet-800/50">
              <CardHeader>
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  {tool.title}
                </h2>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  {tool.description}
                </p>
                <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-violet-600 dark:text-violet-400">
                  Open
                  <span aria-hidden>→</span>
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
