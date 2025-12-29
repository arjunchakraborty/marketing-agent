import { AppShell } from "@/components/layout/AppShell";
import { FileUploader } from "@/components/upload/FileUploader";
import Link from "next/link";

export default function UploadPage() {
  return (
    <AppShell>
      <div className="w-full max-w-4xl mx-auto">
        <div className="mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                Upload Sales Data
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300">
                Upload your sales data files in CSV, Excel, JSON, or image formats. 
                Files will be automatically processed and ingested into the database.
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
              <strong>Step 1 of 4:</strong> After uploading data, proceed to upload campaign images, then run analysis, and finally create targeted campaigns.
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

