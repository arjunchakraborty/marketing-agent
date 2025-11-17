import type { ExperimentPlan } from "@/types/analytics";

interface ExperimentListProps {
  experiments: ExperimentPlan[];
}

const statusStyles: Record<ExperimentPlan["status"], string> = {
  draft: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",
  testing: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  complete: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
};

export function ExperimentList({ experiments }: ExperimentListProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-700/50">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Experiment Planner</h3>
      </div>
      <ul className="divide-y divide-slate-200 dark:divide-slate-700">
        {experiments.map((experiment) => (
          <li key={experiment.id} className="flex flex-col gap-2 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{experiment.name}</p>
              <p className="text-sm text-slate-600 dark:text-slate-300">{experiment.hypothesis}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Primary metric: {experiment.primaryMetric}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusStyles[experiment.status]}`}>
                {experiment.status.toUpperCase()}
              </span>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{experiment.eta}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
