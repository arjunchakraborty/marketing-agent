import { DataUpload } from "@/components/dashboard/DataUpload";

export default function DataUploadPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Data Upload
        </h1>
        <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">
          Upload campaign or product data as zip files.
        </p>
      </div>
      <section>
        <DataUpload />
      </section>
    </div>
  );
}
