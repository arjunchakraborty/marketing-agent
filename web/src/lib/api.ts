const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE}/v1/health`);
  return handleResponse<{ status: string; timestamp: string }>(response);
}

export async function fetchKpis(metrics: string[], filters?: Record<string, string>) {
  const response = await fetch(`${API_BASE}/v1/analytics/kpi`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ metrics, filters: filters || {} }),
  });
  return handleResponse<{ kpis: Record<string, number>; generated_at: string }>(response);
}

export async function fetchPrecomputedKpis(business?: string) {
  const url = business
    ? `${API_BASE}/v1/analytics/kpi/precomputed?business=${encodeURIComponent(business)}`
    : `${API_BASE}/v1/analytics/kpi/precomputed`;
  const response = await fetch(url);
  return handleResponse<{
    kpis: Array<{
      kpi_name: string;
      prompt: string;
      sql_query: string;
      business: string | null;
      created_at: string;
      updated_at: string;
      last_executed_at: string | null;
      execution_count: number;
    }>;
  }>(response);
}

export async function precomputeKpis(business?: string, kpiNames?: string[]) {
  const response = await fetch(`${API_BASE}/v1/analytics/kpi/precompute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business, kpi_names: kpiNames }),
  });
  return handleResponse<{
    results: Array<{
      kpi_name: string;
      prompt: string;
      sql_query: string;
      business: string | null;
      status: string;
      error?: string;
    }>;
    status: string;
  }>(response);
}

export async function fetchCohorts(groupBy: string, metric: string) {
  const response = await fetch(`${API_BASE}/v1/analytics/cohort`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_by: groupBy, metric }),
  });
  return handleResponse<{ group_key: string; cohorts: unknown[] }>(response);
}

export async function generateSqlFromPrompt(prompt: string) {
  const response = await fetch(`${API_BASE}/v1/analytics/prompt-sql`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  return handleResponse<{
    table_name: string;
    business: string;
    dataset_name: string;
    sql: string;
    columns: string[];
    rows: Record<string, unknown>[];
  }>(response);
}
