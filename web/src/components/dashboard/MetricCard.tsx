import clsx from "clsx";
import type { MetricTrend } from "@/types/analytics";

const trendStyles: Record<MetricTrend["trend"], string> = {
  up: "text-emerald-500",
  down: "text-rose-500",
  flat: "text-slate-500",
};

const trendIcons: Record<MetricTrend["trend"], string> = {
  up: "▲",
  down: "▼",
  flat: "■",
};

interface MetricCardProps {
  metric: MetricTrend;
}

export function MetricCard({ metric }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{metric.label}</p>
        <span className={clsx("text-xs font-semibold", trendStyles[metric.trend])}>
          {trendIcons[metric.trend]} {metric.delta}%
        </span>
      </div>
      <p className="mt-4 text-3xl font-semibold text-slate-900 dark:text-slate-100">
        {metric.value.toLocaleString(undefined, { maximumFractionDigits: 1 })}
      </p>
    </div>
  );
}
