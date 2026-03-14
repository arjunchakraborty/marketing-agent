import { CampaignStrategyExperiment } from "@/components/dashboard/CampaignStrategyExperiment";

export default function CampaignStrategyPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Campaign Strategy</h1>
        <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">
          Experiment with campaign strategies and prompts.
        </p>
      </div>
      <section>
        <CampaignStrategyExperiment />
      </section>
    </div>
  );
}
