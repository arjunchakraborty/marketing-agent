import { AppShell } from "@/components/layout/AppShell";
import { InventoryAlerts } from "@/components/dashboard/InventoryAlerts";
import { RecommendationBoard } from "@/components/dashboard/RecommendationBoard";
import { DataUpload } from "@/components/dashboard/DataUpload";
import {
  inventoryAlerts,
} from "@/lib/seedData";
import { PromptSqlExplorer } from "@/components/dashboard/PromptSqlExplorer";
import { CampaignStrategyExperiment } from "@/components/dashboard/CampaignStrategyExperiment";

export default function Home() {
  return (
    <AppShell>
      <section id="data-upload" className="mb-10">
        <DataUpload />
      </section>

      <section id="sql-explorer" className="mt-10 grid gap-6 lg:grid-cols-[2fr_1fr]">
        <PromptSqlExplorer />
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Protocol Status</h3>
            <ul className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
              <li>
                <span className="font-semibold text-slate-800 dark:text-slate-100">A2A:</span> Contract scaffolding online, streaming updates pending queue wiring.
              </li>
              <li>
                <span className="font-semibold text-slate-800 dark:text-slate-100">MCP-AGUI:</span> UI adapters exposed; register with backend `GET /api/v1/health`.
              </li>
              <li>
                <span className="font-semibold text-slate-800 dark:text-slate-100">OpenAI Realtime:</span> Adapter planned for milestone 4.
              </li>
            </ul>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Next Integrations</h3>
            <ul className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
              <li>• Klaviyo publish workflows with asset QA</li>
              <li>• Social credential vaulting + rollback guardrails</li>
              <li>• Custom plugin marketplace for new data sources</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Experiment and Cohort Insights 
      <section id="experiments" className="mt-10 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <ExperimentList experiments={experimentPlans} />
        <CohortTable cohorts={cohortInsights} />
      </section>
      */}

      <section id="campaign-strategy-experiment" className="mt-10">
        <CampaignStrategyExperiment />
      </section>

      <section id="campaigns" className="mt-10">
        <RecommendationBoard />
      </section>

      <section id="inventory" className="mt-10">
        <InventoryAlerts alerts={inventoryAlerts} />
      </section>
    </AppShell>
  );
}
