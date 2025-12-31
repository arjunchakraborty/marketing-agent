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

export interface VectorSearchRequest {
  query: string;
  collection_name?: string;
  num_results?: number;
}

export interface CampaignSearchResult {
  campaign_id: string;
  analysis: any;
  metadata: any;
  similarity_score: number;
}

export interface VectorSearchResponse {
  campaigns: CampaignSearchResult[];
  total_found: number;
  query: string;
}

export async function searchCampaigns(
  request: VectorSearchRequest
): Promise<VectorSearchResponse> {
  const response = await fetch(`${API_BASE}/v1/campaigns/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return handleResponse<VectorSearchResponse>(response);
}

export async function listCollections(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/v1/campaigns/collections`);
  return handleResponse<string[]>(response);
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

export interface ProductZipUploadResponse {
  status: string;
  extracted_path: string;
  processed_at: string;
  details: {
    products_processed: number;
    images_stored: number;
    collection_name: string;
    product_ids: string[];
  };
}

export async function uploadCampaignDataZip(
  file: File,
  businessName?: string,
  collectionName?: string
): Promise<CampaignDataZipUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("table_name", "campaigns");
  formData.append("overwrite_existing", "true");

  const queryParams = new URLSearchParams();
  if (businessName) {
    queryParams.append("business_name", businessName);
  }
  if (collectionName) {
    queryParams.append("collection_name", collectionName);
  }

  const queryString = queryParams.toString();
  const url = queryString 
    ? `${API_BASE}/v1/ingestion/upload/klaviyo?${queryString}`
    : `${API_BASE}/v1/ingestion/upload/klaviyo`;

  const response = await fetch(url, {
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

export async function uploadProductsZip(
  file: File,
  businessName?: string,
  collectionName?: string
): Promise<ProductZipUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const queryParams = new URLSearchParams();
  if (businessName) {
    queryParams.append("business_name", businessName);
  }
  if (collectionName) {
    queryParams.append("collection_name", collectionName);
  }

  const queryString = queryParams.toString();
  const url = queryString 
    ? `${API_BASE}/v1/ingestion/upload/products?${queryString}`
    : `${API_BASE}/v1/ingestion/upload/products`;

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });
  return handleResponse<ProductZipUploadResponse>(response);
}

// Experiments API Functions
export interface ExperimentRunRequest {
  prompt_query: string;
  collection_name?: string;
  experiment_name?: string;
  num_campaigns?: number;
}

export interface KeyFeatures {
  key_features: string[];
  patterns: {
    visual?: string;
    messaging?: string;
    design?: string;
  };
  recommendations: string[];
  summary: string;
}

export interface ExperimentRunResponse {
  experiment_run_id: string;
  status: string;
  campaigns_analyzed: number;
  images_analyzed: number;
  visual_elements_found: number;
  campaign_ids: string[];
  products_promoted: string[];
  key_features?: KeyFeatures;
  error?: string;
}

export async function runExperiment(
  request: ExperimentRunRequest
): Promise<ExperimentRunResponse> {
  const response = await fetch(`${API_BASE}/v1/experiments/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return handleResponse<ExperimentRunResponse>(response);
}

export interface ExperimentResultsResponse {
  experiment_run: {
    experiment_run_id: string;
    name: string | null;
    description: string | null;
    sql_query: string | null;
    status: string;
    config: any;
    results_summary: any;
    created_at: string | null;
    updated_at: string | null;
    completed_at: string | null;
  };
  campaign_analyses: any[];
  image_analyses: any[];
  correlations: any[];
}

export async function getExperimentResults(
  experimentRunId: string
): Promise<ExperimentResultsResponse> {
  const response = await fetch(`${API_BASE}/v1/experiments/${experimentRunId}`);
  return handleResponse<ExperimentResultsResponse>(response);
}

export async function listExperiments(): Promise<ExperimentResultsResponse[]> {
  const response = await fetch(`${API_BASE}/v1/experiments/`);
  return handleResponse<ExperimentResultsResponse[]>(response);
}

export interface CampaignGenerationRequest {
  experiment_run_id: string;
  target_products?: string[];
  use_top_products?: boolean;
  strategy_focus?: string;
  num_campaigns?: number;
}

export interface CampaignGenerationResponse {
  campaigns: Array<{
    name: string;
    channel: string;
    objective: string;
    expected_uplift: string;
    summary: string;
    talking_points: string[];
  }>;
  strategy_insights: string;
  generated_at: string;
}

// Email Campaign Generation (using CampaignGenerationService)
export interface EmailCampaignGenerationRequest {
  campaign_name?: string;
  objective: string;
  audience_segment?: string;
  products?: string[];
  product_images?: string[];
  tone?: string;
  key_message?: string;
  call_to_action?: string;
  include_promotion?: boolean;
  promotion_details?: string;
  subject_line_suggestions?: number;
  include_preview_text?: boolean;
  design_guidance?: string;
  use_past_campaigns?: boolean;
  num_similar_campaigns?: number;
  generate_hero_image?: boolean;
  hero_image_prompt?: string;
}

export interface EmailContent {
  subject_line: string;
  preview_text?: string;
  greeting: string;
  body: string;
  call_to_action: string;
  closing: string;
  footer?: string;
  html_template?: string;
  hero_image_url?: string;
  product_image_urls?: string[];
}

export interface PastCampaignReference {
  campaign_id: string;
  campaign_name?: string;
  similarity_score: number;
  insights_used: string[];
}

export interface EmailCampaignResponse {
  campaign_id: string;
  campaign_name: string;
  objective: string;
  audience_segment?: string;
  email_content: EmailContent;
  subject_line_variations: string[];
  design_recommendations: string[];
  talking_points: string[];
  expected_metrics?: {
    estimated_open_rate?: string;
    estimated_click_rate?: string;
    estimated_conversion_rate?: string;
  };
  past_campaign_references: PastCampaignReference[];
  generated_at: string;
}

export async function generateCampaigns(
  request: CampaignGenerationRequest
): Promise<CampaignGenerationResponse> {
  const response = await fetch(`${API_BASE}/v1/experiments/generate-campaigns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return handleResponse<CampaignGenerationResponse>(response);
}

export async function generateEmailCampaign(
  request: EmailCampaignGenerationRequest
): Promise<EmailCampaignResponse> {
  const response = await fetch(`${API_BASE}/v1/campaigns/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return handleResponse<EmailCampaignResponse>(response);
}
