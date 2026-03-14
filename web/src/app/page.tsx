import Link from "next/link";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export default function HeroPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-50 via-white to-zinc-100 dark:from-zinc-950 dark:via-zinc-900 dark:to-zinc-950">
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-zinc-200/80 bg-white/80 px-6 py-4 backdrop-blur-md dark:border-zinc-800 dark:bg-zinc-950/80">
        <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
          Email Campaigns · Shopify
        </span>
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50 hover:border-zinc-300 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800"
          >
            Open dashboard
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 pt-24 pb-20 text-center sm:pt-32 sm:pb-28">
        <p className="text-sm font-medium uppercase tracking-widest text-violet-600 dark:text-violet-400">
          Marketing intelligence
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight text-zinc-900 dark:text-white sm:text-5xl sm:leading-tight">
          Email campaigns, powered by your data
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-lg text-zinc-600 dark:text-zinc-400">
          Create new campaigns from scratch or leverage existing campaigns—ingest, analyze, and generate in one workspace.
        </p>
        <div className="mt-12 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/dashboard/recommendations"
            className="w-full rounded-xl bg-violet-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-violet-500/25 hover:bg-violet-700 dark:bg-violet-500 dark:shadow-violet-500/20 dark:hover:bg-violet-600 sm:w-auto transition-colors"
          >
            New email campaign
          </Link>
          <Link
            href="/dashboard/leverage"
            className="w-full rounded-xl border-2 border-zinc-200 bg-white px-8 py-4 text-base font-semibold text-zinc-700 hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800 sm:w-auto transition-colors"
          >
            Leverage existing campaigns
          </Link>
        </div>
      </main>

      <section className="border-t border-zinc-200 bg-white/60 dark:border-zinc-800 dark:bg-zinc-950/60 backdrop-blur-sm">
        <div className="mx-auto max-w-5xl px-6 py-20">
          <h2 className="text-center text-xs font-semibold uppercase tracking-widest text-zinc-400 dark:text-zinc-500">
            Two ways to work
          </h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-2">
            <div className="group rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900/50 dark:hover:shadow-zinc-900/50">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-400">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-zinc-900 dark:text-white">
                New email campaign
              </h3>
              <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
                Connect your store, define audience and goal, then create and send. No past data required.
              </p>
              <Link
                href="/dashboard/recommendations"
                className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-violet-600 hover:text-violet-700 dark:text-violet-400 dark:hover:text-violet-300"
              >
                Create campaign
                <span aria-hidden>→</span>
              </Link>
            </div>
            <div className="group rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900/50 dark:hover:shadow-zinc-900/50">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-400">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16m-7 6h7" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-zinc-900 dark:text-white">
                Leverage existing campaigns
              </h3>
              <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
                Upload past campaign data, search with natural language, run experiments, and generate new campaigns from what already works.
              </p>
              <Link
                href="/dashboard/leverage"
                className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-violet-600 hover:text-violet-700 dark:text-violet-400 dark:hover:text-violet-300"
              >
                Explore tools
                <span aria-hidden>→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
