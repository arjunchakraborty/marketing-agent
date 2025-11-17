'use client';

import { useEffect, useState } from 'react';
import { MetricCard } from './MetricCard';
import { generateSqlFromPrompt } from '@/lib/api';
import type { MetricTrend } from '@/types/analytics';

interface MetricsOverviewProps {
  className?: string;
}

// Define prompts for each metric
const METRIC_PROMPTS: Record<string, string> = {
  Revenue: 'What is the total revenue from all campaigns for business Avalon_Sunshine in the last 30 days?',
  AOV: 'What is the average order value (AOV) from all campaigns for business Avalon_Sunshine in the last 30 days?',
  ROAS: 'What is the average return on ad spend (ROAS) from all campaigns in the last 30 days?',
  'Email CTR': 'What is the average email click-through rate (CTR) from all email campaigns in the last 30 days?',
};

// Previous period prompts for calculating deltas
const PREVIOUS_PERIOD_PROMPTS: Record<string, string> = {
  Revenue: 'What is the total revenue from all campaigns for business Avalon_Sunshine in the 30 days before the last 30 days?',
  AOV: 'What is the average order value (AOV) from all campaigns for business Avalon_Sunshine in the 30 days before the last 30 days?',
  ROAS: 'What is the average return on ad spend (ROAS) from all campaigns in the 30 days before the last 30 days?',
  'Email CTR': 'What is the average email click-through rate (CTR) from all email campaigns in the 30 days before the last 30 days?',
};

function extractNumericValue(rows: Record<string, unknown>[]): number {
  if (!rows || rows.length === 0) return 0;
  
  const firstRow = rows[0];
  // Try to find a numeric value in the first row
  // Check common column names first
  const commonKeys = ['value', 'total', 'sum', 'avg', 'average', 'count', 'revenue', 'aov', 'roas', 'ctr'];
  
  for (const key of commonKeys) {
    const value = firstRow[key];
    if (value !== undefined && value !== null) {
      if (typeof value === 'number') {
        return value;
      }
      if (typeof value === 'string') {
        const parsed = parseFloat(value.replace(/[^0-9.-]/g, ''));
        if (!isNaN(parsed)) {
          return parsed;
        }
      }
    }
  }
  
  // Fallback: try all values
  const values = Object.values(firstRow);
  for (const value of values) {
    if (typeof value === 'number') {
      return value;
    }
    if (typeof value === 'string') {
      const parsed = parseFloat(value.replace(/[^0-9.-]/g, ''));
      if (!isNaN(parsed)) {
        return parsed;
      }
    }
  }
  return 0;
}

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

export function MetricsOverview({ className }: MetricsOverviewProps) {
  const [metrics, setMetrics] = useState<MetricTrend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAllMetrics() {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch all metrics in parallel (current period)
        const currentPromises = Object.entries(METRIC_PROMPTS).map(async ([label, prompt]) => {
          try {
            const result = await generateSqlFromPrompt(prompt);
            const value = extractNumericValue(result.rows);
            return { label, value, prompt, success: true };
          } catch (err) {
            console.error(`Failed to fetch ${label}:`, err);
            return { label, value: 0, prompt, success: false };
          }
        });

        // Fetch previous period metrics in parallel
        const previousPromises = Object.entries(PREVIOUS_PERIOD_PROMPTS).map(async ([label, prompt]) => {
          try {
            const result = await generateSqlFromPrompt(prompt);
            const value = extractNumericValue(result.rows);
            return { label, value, success: true };
          } catch (err) {
            console.error(`Failed to fetch previous period for ${label}:`, err);
            return { label, value: 0, success: false };
          }
        });

        const [currentResults, previousResults] = await Promise.all([
          Promise.all(currentPromises),
          Promise.all(previousPromises),
        ]);

        // Create a map of previous values for easy lookup
        const previousMap = new Map(previousResults.map((r) => [r.label, r.value]));

        // Combine current and previous to calculate trends
        const metricsData: MetricTrend[] = currentResults
          .filter((current) => current.success) // Only include successfully fetched metrics
          .map((current) => {
            const previous = previousMap.get(current.label) || 0;
            const { delta, trend } = calculateTrend(current.value, previous);
            
            return {
              label: current.label,
              value: current.value,
              delta,
              trend,
            };
          });

        setMetrics(metricsData);
      } catch (err) {
        console.error('Failed to fetch metrics:', err);
        setError(err instanceof Error ? err.message : 'Failed to load metrics');
      } finally {
        setIsLoading(false);
      }
    }

    fetchAllMetrics();
  }, []);

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

