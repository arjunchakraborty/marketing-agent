import { AppShell } from "@/components/layout/AppShell";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageHelp } from "@/components/common/PageHelp";
import { FileUploader } from "@/components/upload/FileUploader";
import Link from "next/link";

export default function UploadPage() {
  return (
    <AppShell>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Workflow", href: "/workflow" },
          { label: "Upload Data" },
        ]}
      />

      <div className="w-full max-w-4xl mx-auto">
        <div className="mb-6 md:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4 md:mb-6">
            <div className="flex-1">
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2 md:mb-3">
                Upload Sales Data
              </h1>
              <p className="text-sm md:text-base text-slate-600 dark:text-slate-300">
                Upload your sales data files in CSV, Excel, JSON, or image formats. 
                Files will be automatically processed and ingested into the database.
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
            title="Upload Sales Data"
            description="This page allows you to upload sales, campaign, or product data files. Use this when you want to import data directly without going through the full workflow."
            whenToUse={[
              "You have data files ready to upload",
              "You want to import data independently",
              "You're following the workflow (Step 1 of 4)"
            ]}
            relatedPages={[
              { label: "Workflow Guide", href: "/workflow" },
              { label: "Campaign Images", href: "/campaigns/images" },
              { label: "Dashboard", href: "/dashboard" }
            ]}
          />

          <div className="p-3 md:p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg">
            <p className="text-xs md:text-sm text-slate-700 dark:text-slate-300">
              <strong>💡 Tip:</strong> For a guided experience, use the <Link href="/workflow" className="text-blue-600 dark:text-blue-400 hover:underline">Workflow Guide</Link> which walks you through all steps. This page is for direct data upload.
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm">
          <FileUploader />
        </div>

        <div className="mt-8 p-4 md:p-6 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
            Supported File Formats
          </h2>
          <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <li>• <strong>CSV</strong> - Comma-separated values files (.csv)</li>
            <li>• <strong>Excel</strong> - Microsoft Excel files (.xlsx, .xls)</li>
            <li>• <strong>JSON</strong> - JavaScript Object Notation files (.json)</li>
            <li>• <strong>Images</strong> - PNG, JPG, JPEG, GIF, WebP files</li>
          </ul>
        </div>
      </div>
    </AppShell>
  );
}

