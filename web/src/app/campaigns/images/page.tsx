import { AppShell } from "@/components/layout/AppShell";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { ImageUploader } from "@/components/campaigns/ImageUploader";
import Link from "next/link";

export default function CampaignImagesPage() {
  return (
    <AppShell>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Campaigns", href: "/campaigns/demo" },
          { label: "Campaign Images" },
        ]}
      />

      <div className="w-full max-w-6xl mx-auto">
        <div className="mb-6 md:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4 md:mb-6">
            <div className="flex-1">
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2 md:mb-3">
                Campaign Image Analysis
              </h1>
              <p className="text-sm md:text-base text-slate-600 dark:text-slate-300">
                Upload campaign images to analyze visual elements, detect features, and gain insights 
                into what makes successful campaigns.
              </p>
            </div>
            <Link
              href="/workflow"
              className="min-h-[44px] px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors whitespace-nowrap"
            >
              View Workflow →
            </Link>
          </div>
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Step 2 of 4:</strong> After uploading images, run a campaign strategy experiment to correlate visual elements with performance, then create targeted campaigns.
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm">
          <ImageUploader />
        </div>

        <div className="mt-8 p-4 md:p-6 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
            Image Analysis Features
          </h2>
          <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <li>• Visual element detection (CTAs, products, branding)</li>
            <li>• Color palette analysis</li>
            <li>• Composition and layout insights</li>
            <li>• Text content extraction</li>
            <li>• Marketing relevance scoring</li>
          </ul>
        </div>
      </div>
    </AppShell>
  );
}

