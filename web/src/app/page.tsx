import { AppShell } from "@/components/layout/AppShell";
import { CohortTable } from "@/components/dashboard/CohortTable";
import { ExperimentList } from "@/components/dashboard/ExperimentList";
import { InventoryAlerts } from "@/components/dashboard/InventoryAlerts";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { RecommendationBoard } from "@/components/dashboard/RecommendationBoard";
import {
  campaignRecommendations,
  cohortInsights,
  experimentPlans,
  inventoryAlerts,
  metricTrends,
} from "@/lib/seedData";
import { PromptSqlExplorer } from "@/components/dashboard/PromptSqlExplorer";

export default function Home() {
  return (
    <AppShell>
      <section id="overview" className="grid gap-6 lg:grid-cols-4">
        {metricTrends.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section id="sql-explorer" className="mt-10 grid gap-6 lg:grid-cols-[2fr_1fr]">
        <PromptSqlExplorer />
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700">Protocol Status</h3>
            <ul className="mt-4 space-y-3 text-sm text-slate-600">
              <li>
                <span className="font-semibold text-slate-800">A2A:</span> Contract scaffolding online, streaming updates pending queue wiring.
              </li>
              <li>
                <span className="font-semibold text-slate-800">MCP-AGUI:</span> UI adapters exposed; register with backend `GET /api/v1/health`.
              </li>
              <li>
                <span className="font-semibold text-slate-800">OpenAI Realtime:</span> Adapter planned for milestone 4.
              </li>
            </ul>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700">Next Integrations</h3>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              <li>• Klaviyo publish workflows with asset QA</li>
              <li>• Social credential vaulting + rollback guardrails</li>
              <li>• Custom plugin marketplace for new data sources</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="experiments" className="mt-10 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <ExperimentList experiments={experimentPlans} />
        <CohortTable cohorts={cohortInsights} />
      </section>

      <section id="campaigns" className="mt-10">
        <RecommendationBoard recommendations={campaignRecommendations} />
      </section>

      <section id="inventory" className="mt-10">
        <InventoryAlerts alerts={inventoryAlerts} />
      </section>
    </AppShell>
  );
}
