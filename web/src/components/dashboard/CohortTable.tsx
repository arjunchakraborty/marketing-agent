import type { CohortInsight } from "@/types/analytics";

interface CohortTableProps {
  cohorts: CohortInsight[];
}

export function CohortTable({ cohorts }: CohortTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-700/50">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Cohort Performance</h3>
      </div>
      <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
        <thead className="bg-white dark:bg-slate-800">
          <tr className="text-left text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
            <th className="px-4 py-2">Cohort</th>
            <th className="px-4 py-2">Conversion</th>
            <th className="px-4 py-2">Lift vs Baseline</th>
            <th className="px-4 py-2">Members</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white dark:divide-slate-700 dark:bg-slate-800">
          {cohorts.map((cohort) => (
            <tr key={cohort.cohort}>
              <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">{cohort.cohort}</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{cohort.conversionRate.toFixed(1)}%</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{cohort.lift >= 0 ? "+" : ""}{cohort.lift.toFixed(1)}%</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{cohort.size.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
