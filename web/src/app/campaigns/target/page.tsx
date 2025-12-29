import { AppShell } from "@/components/layout/AppShell";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageHelp } from "@/components/common/PageHelp";
import { TargetCampaignBuilder } from "@/components/campaigns/TargetCampaignBuilder";
import Link from "next/link";

export default function TargetCampaignPage() {
  return (
    <AppShell>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Campaigns", href: "/campaigns/demo" },
          { label: "Create Campaign" },
        ]}
      />

      <div className="w-full max-w-4xl mx-auto">
        <div className="mb-6 md:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4 md:mb-6">
            <div className="flex-1">
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2 md:mb-3">
                Create Targeted Campaign
              </h1>
              <p className="text-sm md:text-base text-slate-600 dark:text-slate-300">
                Build targeted campaigns by selecting audience segments and defining campaign objectives. 
                Analyze targeting effectiveness before launching.
              </p>
            </div>
            <Link
              href="/workflow"
              className="min-h-[44px] px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors whitespace-nowrap"
            >
              View Workflow →
            </Link>
          </div>

          <PageHelp
            title="Create Targeted Campaign"
            description="Create a new marketing campaign by selecting audience segments, products, and objectives. You can upload product images and analyze targeting effectiveness before launching."
            whenToUse={[
              "You're ready to create a new campaign",
              "You have audience segments identified",
              "You want to test campaign targeting before launch",
              "You're completing the workflow (Step 4 of 4)"
            ]}
            relatedPages={[
              { label: "Campaign Demo", href: "/campaigns/demo" },
              { label: "Email Preview", href: "/campaigns/email-preview" },
              { label: "Workflow Guide", href: "/workflow" }
            ]}
          />

          <div className="p-3 md:p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg">
            <p className="text-xs md:text-sm text-slate-700 dark:text-slate-300">
              <strong>💡 Tip:</strong> Try the <Link href="/campaigns/demo" className="text-blue-600 dark:text-blue-400 hover:underline">Campaign Demo</Link> first to see how it works with sample data.
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

