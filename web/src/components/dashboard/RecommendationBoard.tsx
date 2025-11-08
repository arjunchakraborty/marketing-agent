import clsx from "clsx";
import type { CampaignRecommendation } from "@/types/analytics";

interface RecommendationBoardProps {
  recommendations: CampaignRecommendation[];
}

const statusStyles: Record<CampaignRecommendation["status"], string> = {
  planned: "border-sky-200 bg-sky-50 text-sky-700",
  "in-flight": "border-emerald-200 bg-emerald-50 text-emerald-700",
  blocked: "border-rose-200 bg-rose-50 text-rose-700",
};

export function RecommendationBoard({ recommendations }: RecommendationBoardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-700">Campaign Recommendations</h3>
      </div>
      <div className="grid gap-4 p-4 sm:grid-cols-2">
        {recommendations.map((recommendation) => (
          <article
            key={recommendation.id}
            className={clsx(
              "rounded-lg border p-4 shadow-sm transition hover:shadow-md",
              statusStyles[recommendation.status],
            )}
          >
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide">{recommendation.channel}</p>
              <span className="text-xs font-medium">{recommendation.expectedUplift}</span>
            </div>
            <h4 className="mt-2 text-base font-semibold text-slate-800">{recommendation.objective}</h4>
            <p className="mt-1 text-sm text-slate-600">{recommendation.summary}</p>
            <p className="mt-4 text-xs font-medium text-slate-500">Status: {recommendation.status}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
