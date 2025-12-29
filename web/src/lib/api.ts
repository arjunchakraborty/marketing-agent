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

// Data Upload API Functions
export interface CampaignDataZipUploadResponse {
  status: string;
  csv_ingestion?: {
    status: string;
    table_name: string;
    total_rows: number;
    inserted: number;
    updated: number;
    errors?: string[] | null;
    columns: string[];
    ingested_at: string;
  };
  vector_db_loading?: {
    status: string;
    total_campaigns: number;
    loaded: number;
    skipped: number;
    errors: number;
    campaigns_with_images: number;
    campaigns_without_images: number;
    error_details?: Array<{ campaign_id: string; error: string }>;
    collection_name: string;
    vector_db_path: string;
  };
  processed_at: string;
}

export interface ShopifyIntegrationZipUploadResponse {
  status: string;
  extracted_path: string;
  processed_at: string;
  details: {
    ingested_count: number;
    datasets: Array<{
      table_name: string;
      business: string;
      category: string;
      dataset_name: string;
      row_count: number;
      columns: string[];
    }>;
  };
}

export interface VectorDbZipUploadResponse {
  status: string;
  extracted_path: string;
  processed_at: string;
  details: {
    status: string;
    total_campaigns: number;
    loaded: number;
    skipped: number;
    errors: number;
    campaigns_with_images: number;
    campaigns_without_images: number;
    error_details?: Array<{ campaign_id: string; error: string }>;
    collection_name: string;
    vector_db_path: string;
  };
}

export async function uploadCampaignDataZip(
  file: File
): Promise<CampaignDataZipUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("table_name", "campaigns");
  formData.append("collection_name", "campaign_data");
  formData.append("overwrite_existing", "true");

  const response = await fetch(`${API_BASE}/v1/ingestion/upload/klaviyo`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<CampaignDataZipUploadResponse>(response);
}

export async function uploadShopifyIntegrationZip(
  file: File,
  business?: string
): Promise<ShopifyIntegrationZipUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (business) {
    formData.append("business", business);
  }

  const response = await fetch(`${API_BASE}/v1/ingestion/upload/shopify-integration`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<ShopifyIntegrationZipUploadResponse>(response);
}

export async function uploadVectorDbZip(
  file: File
): Promise<VectorDbZipUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("collection_name", "campaign_data");
  formData.append("overwrite_existing", "true");

  const response = await fetch(`${API_BASE}/v1/ingestion/upload/vector-db`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<VectorDbZipUploadResponse>(response);
}
