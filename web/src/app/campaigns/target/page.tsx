import { AppShell } from "@/components/layout/AppShell";
import { TargetCampaignBuilder } from "@/components/campaigns/TargetCampaignBuilder";
import Link from "next/link";

export default function TargetCampaignPage() {
  return (
    <AppShell>
      <div className="w-full max-w-4xl mx-auto">
        <div className="mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                Create Targeted Campaign
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300">
                Build targeted campaigns by selecting audience segments and defining campaign objectives. 
                Analyze targeting effectiveness before launching.
              </p>
            </div>
            <Link
              href="/workflow"
              className="px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20"
            >
              View Workflow →
            </Link>
          </div>
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Step 4 of 4:</strong> Use insights from your data upload, image analysis, and campaign strategy experiments to create targeted campaigns.
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm">
          <TargetCampaignBuilder />
        </div>
      </div>
    </AppShell>
  );
}

