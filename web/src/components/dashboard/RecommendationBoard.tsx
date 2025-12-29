"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import type { CampaignRecommendation } from "@/types/analytics";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:2121/api";

interface RecommendationBoardProps {
  recommendations?: CampaignRecommendation[]; // Optional for backward compatibility
}

interface ApiRecommendation {
  name: string;
  channel: string;
  expected_uplift: number;
  talking_points: string[];
}

const statusStyles: Record<CampaignRecommendation["status"], string> = {
  planned: "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-800 dark:bg-sky-900/30 dark:text-sky-300",
  "in-flight": "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  blocked: "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-900/30 dark:text-rose-300",
};

export function RecommendationBoard({ recommendations: propRecommendations }: RecommendationBoardProps) {
  const [recommendations, setRecommendations] = useState<CampaignRecommendation[]>(propRecommendations || []);
  const [isLoading, setIsLoading] = useState(!propRecommendations);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log("[RecommendationBoard] Fetching recommendations from API...");
      const response = await fetch(`${API_BASE}/v1/intelligence/campaigns`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          objectives: ["Increase conversion rate", "Maximize revenue", "Improve customer engagement"],
          audience_segments: ["High-value customers", "Price-sensitive shoppers", "New subscribers"],
          constraints: {},
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch recommendations: ${response.status}`);
      }

      const data = await response.json();
      console.log("[RecommendationBoard] API response:", data);

      // Transform API response to match CampaignRecommendation type
      const transformed: CampaignRecommendation[] = (data.recommendations || []).map(
        (rec: ApiRecommendation, idx: number) => ({
          id: `rec-${idx}-${Date.now()}`,
          channel: rec.channel || "Unknown",
          objective: rec.name || "Campaign Objective",
          expectedUplift: `+${rec.expected_uplift?.toFixed(1) || 0}%`,
          summary: rec.talking_points?.join(". ") || "AI-generated campaign recommendation",
          status: "planned" as const, // Default status
        })
      );

      setRecommendations(transformed);
      console.log("[RecommendationBoard] Recommendations updated:", transformed.length);
    } catch (err: any) {
      console.error("[RecommendationBoard] Error fetching recommendations:", err);
      setError(err.message || "Failed to load recommendations");
      // Fall back to prop recommendations if available
      if (propRecommendations) {
        setRecommendations(propRecommendations);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if no recommendations were provided as props
    if (!propRecommendations || propRecommendations.length === 0) {
      fetchRecommendations();
    }
  }, []);

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-700/50 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Campaign Recommendations</h3>
        <button
          onClick={fetchRecommendations}
          disabled={isLoading}
          className="text-xs text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 disabled:opacity-50"
        >
          {isLoading ? "Loading..." : "Refresh"}
        </button>
      </div>
      <div className="grid gap-4 p-4 sm:grid-cols-2">
        {isLoading ? (
          <div className="col-span-2 text-center py-8 text-sm text-slate-500 dark:text-slate-400">
            Loading recommendations...
          </div>
        ) : error ? (
          <div className="col-span-2 text-center py-8">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            <button
              onClick={fetchRecommendations}
              className="mt-2 text-xs text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            >
              Try again
            </button>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="col-span-2 text-center py-8 text-sm text-slate-500 dark:text-slate-400">
            No recommendations available. Click "Refresh" to generate new recommendations.
          </div>
        ) : (
          recommendations.map((recommendation) => (
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
              <h4 className="mt-2 text-base font-semibold text-slate-800 dark:text-slate-100">{recommendation.objective}</h4>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{recommendation.summary}</p>
              <p className="mt-4 text-xs font-medium text-slate-500 dark:text-slate-400">Status: {recommendation.status}</p>
            </article>
          ))
        )}
      </div>
    </div>
  );
}
