'use client';

import { useEffect, useState } from 'react';
import { MetricCard } from './MetricCard';
import { fetchKpis } from '@/lib/api';
import type { MetricTrend } from '@/types/analytics';

interface MetricsOverviewProps {
  className?: string;
  business?: string;
}

// Standard KPI metrics that match the backend precomputed KPIs
const STANDARD_METRICS = ['Revenue', 'AOV', 'Conversion Rate', 'Email CTR'];

function calculateTrend(current: number, previous: number): { delta: number; trend: 'up' | 'down' | 'flat' } {
  if (previous === 0) {
    return { delta: 0, trend: 'flat' };
  }
  
  const delta = ((current - previous) / previous) * 100;
  
  if (Math.abs(delta) < 0.1) {
    return { delta: 0, trend: 'flat' };
  }
  
  return {
    delta: Math.round(delta * 10) / 10,
    trend: delta > 0 ? 'up' : 'down',
  };
}

export function MetricsOverview({ className, business }: MetricsOverviewProps) {
  const [metrics, setMetrics] = useState<MetricTrend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAllMetrics() {
      setIsLoading(true);
      setError(null);

      try {
        const filters: Record<string, string> = business ? { business } : {};
        
        // Fetch current period KPIs using the new API endpoint
        const currentKpis = await fetchKpis(STANDARD_METRICS, filters);
        
        // For now, we'll use the current values and set previous to 0
        // In a real implementation, you might want to fetch previous period separately
        // or modify the backend to return both current and previous period values
        const metricsData: MetricTrend[] = STANDARD_METRICS
          .map((metricName) => {
            const value = currentKpis.kpis[metricName] || 0;
            // For now, we'll calculate trend as flat since we don't have previous period data
            // You can enhance this by fetching previous period KPIs separately if needed
            const { delta, trend } = calculateTrend(value, 0);
            
            return {
              label: metricName,
              value,
              delta,
              trend,
            };
          })
          .filter((metric) => metric.value > 0 || metric.label === 'Conversion Rate'); // Filter out zero values except for rates

        setMetrics(metricsData);
      } catch (err) {
        console.error('Failed to fetch metrics:', err);
        setError(err instanceof Error ? err.message : 'Failed to load metrics');
      } finally {
        setIsLoading(false);
      }
    }

    fetchAllMetrics();
  }, [business]);

  if (isLoading) {
    return (
      <div className={`grid gap-6 lg:grid-cols-4 ${className || ''}`}>
        {['Revenue', 'AOV', 'ROAS', 'Email CTR'].map((label) => (
          <div
            key={label}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800 animate-pulse"
          >
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-24 mb-4"></div>
            <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-32"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={`rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-800 dark:bg-rose-900/30 ${className || ''}`}>
        <p className="text-sm font-medium text-rose-700 dark:text-rose-300">
          Error loading metrics: {error}
        </p>
      </div>
    );
  }

  if (metrics.length === 0) {
    return (
      <div className={`rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800 ${className || ''}`}>
        <p className="text-sm text-slate-600 dark:text-slate-300">No metrics available</p>
      </div>
    );
  }

  return (
    <div className={`grid gap-6 lg:grid-cols-4 ${className || ''}`}>
      {metrics.map((metric) => (
        <MetricCard key={metric.label} metric={metric} />
      ))}
    </div>
  );
}

