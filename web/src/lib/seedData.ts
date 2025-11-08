import type {
  CampaignRecommendation,
  CohortInsight,
  ExperimentPlan,
  InventoryAlert,
  MetricTrend,
} from "@/types/analytics";

export const metricTrends: MetricTrend[] = [
  { label: "Revenue", value: 182000, delta: 12.4, trend: "up" },
  { label: "AOV", value: 86.5, delta: 4.1, trend: "up" },
  { label: "ROAS", value: 3.4, delta: -0.6, trend: "down" },
  { label: "Email CTR", value: 4.8, delta: 1.1, trend: "up" },
];

export const cohortInsights: CohortInsight[] = [
  { cohort: "Creators", conversionRate: 5.8, lift: 1.2, size: 1240 },
  { cohort: "VIP Customers", conversionRate: 9.4, lift: 2.6, size: 320 },
  { cohort: "New Subscribers", conversionRate: 3.1, lift: -0.5, size: 2890 },
];

export const experimentPlans: ExperimentPlan[] = [
  {
    id: "exp-042",
    name: "Welcome Flow V3",
    hypothesis: "Personalized product drops boost first purchase conversions",
    primaryMetric: "First Purchase Rate",
    status: "testing",
    eta: "Completes in 3 days",
  },
  {
    id: "exp-037",
    name: "SMS Cart Saver",
    hypothesis: "Time-sensitive discount drives higher recovery",
    primaryMetric: "Recovered Revenue",
    status: "draft",
    eta: "Launch ready",
  },
  {
    id: "exp-018",
    name: "Evergreen Retargeting",
    hypothesis: "Dynamic creatives reduce fatigue",
    primaryMetric: "Blended ROAS",
    status: "complete",
    eta: "Wrapped last week",
  },
];

export const campaignRecommendations: CampaignRecommendation[] = [
  {
    id: "cmp-112",
    channel: "Email",
    objective: "Reactivate lapsed VIPs",
    expectedUplift: "+8.2% revenue",
    summary: "Use brand refresh template with dynamic bundles and loyalty tier callout.",
    status: "planned",
  },
  {
    id: "cmp-119",
    channel: "Paid Social",
    objective: "Boost evergreen retargeting",
    expectedUplift: "+14.7% ROAS",
    summary: "Launch 15s motion ad variant with creator UGC segments.",
    status: "in-flight",
  },
  {
    id: "cmp-109",
    channel: "SMS",
    objective: "Cart recovery",
    expectedUplift: "+6.4% recovery",
    summary: "Enable 2-step SMS reminder with urgency copy and fallback email.",
    status: "blocked",
  },
];

export const inventoryAlerts: InventoryAlert[] = [
  {
    sku: "BR-TEE-XL",
    productName: "Brand Refresh Tee (XL)",
    daysRemaining: 5,
    priority: "high",
  },
  {
    sku: "BR-HOODIE-M",
    productName: "Motion Hoodie (M)",
    daysRemaining: 12,
    priority: "medium",
  },
  {
    sku: "BR-CAP-OS",
    productName: "Studio Cap",
    daysRemaining: 21,
    priority: "low",
  },
];
