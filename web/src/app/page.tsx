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

export default function Home() {
  return (
    <AppShell>
      <section id="overview" className="grid gap-6 lg:grid-cols-4">
        {metricTrends.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section id="sql-explorer" className="mt-10 grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Prompt-to-SQL Explorer</h2>
              <p className="text-sm text-slate-600">
                Translate natural language questions into runnable SQL across your unified Shopify and CSV schemas.
              </p>
            </div>
            <button className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:border-slate-300 hover:text-slate-900">
              Launch Sandbox
            </button>
          </div>
          <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
            <p className="font-semibold text-slate-700">Recent prompt</p>
            <p className="mt-2">
              &ldquo;Show ROAS and blended CPA for creator campaigns over the last 14 days, grouped by audience segment&rdquo;
            </p>
            <div className="mt-4 rounded-lg bg-black p-4 font-mono text-xs text-lime-400">
              <p>SELECT audience_segment, SUM(spend) AS spend, SUM(revenue) AS revenue,</p>
              <p className="pl-4">ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 2) AS roas,</p>
              <p className="pl-4">ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2) AS cpa</p>
              <p>FROM analytics.campaign_performance</p>
              <p>WHERE channel = &lsquo;Paid Social&rsquo; AND tag = &lsquo;creator&rsquo;</p>
              <p>  AND occurred_at BETWEEN CURRENT_DATE - INTERVAL &lsquo;14 days&rsquo; AND CURRENT_DATE</p>
              <p>GROUP BY audience_segment;</p>
            </div>
          </div>
        </div>
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
