import { RecommendationBoard } from "@/components/dashboard/RecommendationBoard";

export default function RecommendationsPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Recommendations</h1>
        <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">
          Campaign recommendations and planning.
        </p>
      </div>
      <section>
        <RecommendationBoard />
      </section>
    </div>
  );
}
