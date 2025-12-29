import { AppShell } from "@/components/layout/AppShell";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageHelp } from "@/components/common/PageHelp";
import { InventoryAlerts } from "@/components/dashboard/InventoryAlerts";
import { RecommendationBoard } from "@/components/dashboard/RecommendationBoard";
import {
  inventoryAlerts,
} from "@/lib/seedData";
import { PromptSqlExplorer } from "@/components/dashboard/PromptSqlExplorer";
import { CampaignStrategyExperiment } from "@/components/dashboard/CampaignStrategyExperiment";
import { MetricsOverview } from "@/components/dashboard/MetricsOverview";
import { ApiConnectionTest } from "@/components/dashboard/ApiConnectionTest";

export default function Dashboard() {
  return (
    <AppShell>
      <Breadcrumbs items={[{ label: "Home", href: "/" }, { label: "Dashboard" }]} />
      
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2 md:mb-3">
          Dashboard
        </h1>
        <p className="text-sm md:text-base text-slate-600 dark:text-slate-300 mb-4">
          Real-time analytics, insights, and campaign performance metrics
        </p>

        <PageHelp
          title="Analytics Dashboard"
          description="Your central hub for viewing KPIs, running SQL queries, analyzing campaign strategies, and getting AI-powered recommendations. All your marketing intelligence in one place."
          whenToUse={[
            "You want to see overall performance metrics",
            "You need to run custom SQL queries on your data",
            "You want to analyze campaign strategies",
            "You're looking for campaign recommendations",
            "You need to check inventory alerts"
          ]}
          relatedPages={[
            { label: "Create Campaign", href: "/campaigns/target" },
            { label: "Upload Data", href: "/upload" },
            { label: "Workflow Guide", href: "/workflow" }
          ]}
        />
      </div>

      <section id="overview" className="w-full mb-6 md:mb-8">
        <div className="mb-4 md:mb-6">
          <ApiConnectionTest />
        </div>
        <MetricsOverview />
      </section>

      <section id="sql-explorer" className="mt-6 md:mt-10 grid gap-6 lg:grid-cols-[2fr_1fr]">
        <PromptSqlExplorer />
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
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
          <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
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

      <section id="campaign-strategy-experiment" className="mt-6 md:mt-10">
        <CampaignStrategyExperiment />
      </section>

      <section id="campaigns" className="mt-6 md:mt-10">
        <RecommendationBoard />
      </section>

      <section id="inventory" className="mt-6 md:mt-10">
        <InventoryAlerts alerts={inventoryAlerts} />
      </section>
    </AppShell>
  );
}

