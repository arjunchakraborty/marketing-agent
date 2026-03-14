import { PromptSqlExplorer } from "@/components/dashboard/PromptSqlExplorer";

export default function SqlExplorerPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">SQL Explorer</h1>
        <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">
          Search campaigns and explore data with natural language.
        </p>
      </div>
      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <PromptSqlExplorer />
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-900/50">
            <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">Protocol Status</h3>
            <ul className="mt-4 space-y-3 text-sm text-zinc-600 dark:text-zinc-400">
              <li>
                <span className="font-semibold text-zinc-800 dark:text-zinc-100">A2A:</span> Contract scaffolding online, streaming updates pending queue wiring.
              </li>
              <li>
                <span className="font-semibold text-zinc-800 dark:text-zinc-100">MCP-AGUI:</span> UI adapters exposed; register with backend `GET /api/v1/health`.
              </li>
              <li>
                <span className="font-semibold text-zinc-800 dark:text-zinc-100">OpenAI Realtime:</span> Adapter planned for milestone 4.
              </li>
            </ul>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-700 dark:bg-zinc-900/50">
            <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">Next Integrations</h3>
            <ul className="mt-4 space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
              <li>• Klaviyo publish workflows with asset QA</li>
              <li>• Social credential vaulting + rollback guardrails</li>
              <li>• Custom plugin marketplace for new data sources</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
