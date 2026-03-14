export type MetricTrend = {
  label: string;
  value: number;
  delta: number;
  trend: "up" | "down" | "flat";
};

export type CohortInsight = {
  cohort: string;
  conversionRate: number;
  lift: number;
  size: number;
};

export type ExperimentPlan = {
  id: string;
  name: string;
  hypothesis: string;
  primaryMetric: string;
  status: "draft" | "testing" | "complete";
  eta: string;
};

export type CampaignRecommendation = {
  id: string;
  channel: string;
  objective: string;
  expectedUplift: string;
  summary: string;
  status: "planned" | "in-flight" | "blocked";
};

export type InventoryAlert = {
  sku: string;
  productName: string;
  daysRemaining: number;
  priority: "high" | "medium" | "low";
};
