const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:2121/api";

// Debug helper - log API base in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('[API] Base URL:', API_BASE);
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const text = await response.text();
      if (text) {
        try {
          const json = JSON.parse(text);
          message = json.detail || json.message || text;
        } catch {
          message = text;
        }
      }
    } catch {
      // Use default message
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function fetchHealth() {
  try {
    const response = await fetch(`${API_BASE}/v1/health`);
    return handleResponse<{ status: string; timestamp: string }>(response);
  } catch (error) {
    console.error('[API] fetchHealth error:', error);
    throw error;
  }
}

export async function fetchKpis(metrics: string[], filters?: Record<string, string>) {
  try {
    const response = await fetch(`${API_BASE}/v1/analytics/kpi`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ metrics, filters: filters || {} }),
    });
    return handleResponse<{ kpis: Record<string, number>; generated_at: string }>(response);
  } catch (error) {
    console.error('[API] fetchKpis error:', error, 'URL:', `${API_BASE}/v1/analytics/kpi`);
    throw error;
  }
}

export async function fetchPrecomputedKpis(business?: string) {
  const url = business
    ? `${API_BASE}/v1/analytics/kpi/precomputed?business=${encodeURIComponent(business)}`
    : `${API_BASE}/v1/analytics/kpi/precomputed`;
  try {
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
  } catch (error) {
    console.error('[API] fetchPrecomputedKpis error:', error);
    throw error;
  }
}

export async function precomputeKpis(business?: string, kpiNames?: string[]) {
  try {
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
  } catch (error) {
    console.error('[API] precomputeKpis error:', error);
    throw error;
  }
}

export async function fetchCohorts(groupBy: string, metric: string) {
  try {
    const response = await fetch(`${API_BASE}/v1/analytics/cohort`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ group_by: groupBy, metric }),
    });
    return handleResponse<{ group_key: string; cohorts: unknown[] }>(response);
  } catch (error) {
    console.error('[API] fetchCohorts error:', error);
    throw error;
  }
}

export async function generateSqlFromPrompt(prompt: string) {
  try {
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
  } catch (error) {
    console.error('[API] generateSqlFromPrompt error:', error);
    throw error;
  }
}

// Sales Upload API
export async function uploadSalesFile(
  file: File,
  business?: string,
  autoIngest: boolean = true
) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    if (business) {
      formData.append("business", business);
    }
    formData.append("auto_ingest", String(autoIngest));

    const response = await fetch(`${API_BASE}/v1/sales/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse<{
      upload_id: string;
      filename: string;
      file_type: string;
      file_size: number;
      status: string;
      ingested: boolean;
      table_name?: string;
      row_count?: number;
      errors?: string[];
      message: string;
    }>(response);
  } catch (error) {
    console.error('[API] uploadSalesFile error:', error);
    throw error;
  }
}

// Campaign Targeting API
export async function getCampaignSegments() {
  try {
    const response = await fetch(`${API_BASE}/v1/campaigns/segments`);
    return handleResponse<{
      segments: Array<{
        segment_id: string;
        name: string;
        description?: string;
        criteria: Record<string, any>;
        size?: number;
      }>;
    }>(response);
  } catch (error) {
    console.error('[API] getCampaignSegments error:', error);
    throw error;
  }
}

export async function createTargetedCampaign(data: {
  campaign_name: string;
  segment_ids: string[];
  channel?: string;
  objective: string;
  constraints?: Record<string, any>;
  products?: string[];
  product_images?: Array<{ product_id: string; image_url: string; alt_text?: string }>;
}) {
  try {
    const response = await fetch(`${API_BASE}/v1/campaigns/target`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse<{
      campaign_id: string;
      campaign_name: string;
      segments: Array<{
        segment_id: string;
        name: string;
        description?: string;
        criteria: Record<string, any>;
        size?: number;
      }>;
      estimated_reach: number;
      status: string;
      created_at: string;
      product_images?: Array<{ product_id: string; image_url: string; alt_text?: string }>;
    }>(response);
  } catch (error) {
    console.error('[API] createTargetedCampaign error:', error);
    throw error;
  }
}

export async function analyzeTargeting(data: {
  campaign_id?: string;
  segment_ids?: string[];
  date_range?: Record<string, string>;
}) {
  try {
    const response = await fetch(`${API_BASE}/v1/campaigns/analyze-targeting`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse<{
      campaign_id?: string;
      segment_performance: Array<Record<string, any>>;
      recommendations: string[];
      summary: string;
    }>(response);
  } catch (error) {
    console.error('[API] analyzeTargeting error:', error);
    throw error;
  }
}

export async function getCampaignPerformance(campaignId: string) {
  try {
    const response = await fetch(`${API_BASE}/v1/campaigns/${campaignId}/performance`);
    return handleResponse<{
      campaign_id: string;
      overall_performance: Record<string, any>;
      segment_performance: Array<Record<string, any>>;
      top_performing_segments: string[];
    }>(response);
  } catch (error) {
    console.error('[API] getCampaignPerformance error:', error);
    throw error;
  }
}
