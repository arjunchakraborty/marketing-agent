"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:2121/api";

export default function CampaignDemoPage() {
  const [segments, setSegments] = useState<any[]>([]);
  const [campaign, setCampaign] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<"segments" | "create" | "analyze" | "complete">("segments");
  const [selectedDemo, setSelectedDemo] = useState<string>("summer-sale");

  // Multiple demo campaign data options
  const demoCampaigns = {
    "summer-sale": {
      id: "summer-sale",
      name: "Summer Sale 2024",
      campaignName: "Summer Sale 2024 - High Value Customers",
      selectedSegments: ["high_value", "frequent_buyers"],
      channel: "email",
      objective: "Increase revenue by 15% through exclusive offers",
      products: ["PROD001", "PROD002", "PROD003"],
      productImages: [
        {
          product_id: "PROD001",
          image_url: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
          alt_text: "Premium Watch",
        },
        {
          product_id: "PROD002",
          image_url: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop",
          alt_text: "Running Shoes",
        },
        {
          product_id: "PROD003",
          image_url: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop",
          alt_text: "Leather Bag",
        },
      ],
      description: "Target high-value customers with premium summer products",
    },
    "flash-sale": {
      id: "flash-sale",
      name: "Flash Sale - Price Sensitive",
      campaignName: "Flash Sale 2024 - Price Sensitive Shoppers",
      selectedSegments: ["price_sensitive", "new_customers"],
      channel: "email",
      objective: "Acquire new customers with limited-time discounts",
      products: ["PROD004", "PROD005", "PROD006"],
      productImages: [
        {
          product_id: "PROD004",
          image_url: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop",
          alt_text: "Wireless Headphones",
        },
        {
          product_id: "PROD005",
          image_url: "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=400&fit=crop",
          alt_text: "Sunglasses",
        },
        {
          product_id: "PROD006",
          image_url: "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=400&h=400&fit=crop",
          alt_text: "Camera",
        },
      ],
      description: "Quick flash sale targeting price-sensitive and new customers",
    },
    "retention": {
      id: "retention",
      name: "Customer Retention",
      campaignName: "Customer Retention Campaign - At Risk Customers",
      selectedSegments: ["at_risk", "high_value"],
      channel: "email",
      objective: "Re-engage at-risk customers with personalized offers",
      products: ["PROD007", "PROD008", "PROD009"],
      productImages: [
        {
          product_id: "PROD007",
          image_url: "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400&h=400&fit=crop",
          alt_text: "Smartphone",
        },
        {
          product_id: "PROD008",
          image_url: "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=400&fit=crop",
          alt_text: "Laptop",
        },
        {
          product_id: "PROD009",
          image_url: "https://images.unsplash.com/photo-1544966503-7cc75cbd34f8?w=400&h=400&fit=crop",
          alt_text: "Tablet",
        },
      ],
      description: "Win back at-risk customers with exclusive retention offers",
    },
    "product-launch": {
      id: "product-launch",
      name: "New Product Launch",
      campaignName: "New Product Launch - All Segments",
      selectedSegments: ["high_value", "frequent_buyers", "new_customers"],
      channel: "email",
      objective: "Promote new product line to all customer segments",
      products: ["PROD010", "PROD011", "PROD012"],
      productImages: [
        {
          product_id: "PROD010",
          image_url: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",
          alt_text: "Fitness Tracker",
        },
        {
          product_id: "PROD011",
          image_url: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop",
          alt_text: "Backpack",
        },
        {
          product_id: "PROD012",
          image_url: "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop",
          alt_text: "Water Bottle",
        },
      ],
      description: "Launch new products across multiple customer segments",
    },
  };

  const demoCampaign = demoCampaigns[selectedDemo as keyof typeof demoCampaigns];

  useEffect(() => {
    loadSegments();
  }, []);

  const loadSegments = async () => {
    try {
      const response = await fetch(`${API_BASE}/v1/campaigns/segments`);
      if (response.ok) {
        const data = await response.json();
        setSegments(data.segments || []);
      }
    } catch (err) {
      console.error("Failed to load segments:", err);
    }
  };

  const createDemoCampaign = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/v1/campaigns/target`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          campaign_name: demoCampaign.campaignName,
          segment_ids: demoCampaign.selectedSegments,
          channel: demoCampaign.channel,
          objective: demoCampaign.objective,
          constraints: {},
          products: demoCampaign.products,
          product_images: demoCampaign.productImages,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create campaign");
      }

      const result = await response.json();
      setCampaign(result);
      setStep("analyze");

      // Automatically run analysis
      if (result.campaign_id) {
        setTimeout(() => {
          analyzeCampaign(result.campaign_id);
        }, 1000);
      }
    } catch (err: any) {
      console.error("Campaign creation error:", err);
      setError(err.message || "Failed to create campaign");
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(`${API_BASE}/v1/campaigns/analyze-targeting`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          campaign_id: campaignId,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setAnalysis(result);
        setStep("complete");
      }
    } catch (err) {
      console.error("Analysis error:", err);
    }
  };

  const getCampaignPerformance = async (campaignId: string) => {
    try {
      const response = await fetch(`${API_BASE}/v1/campaigns/${campaignId}/performance`);
      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (err) {
      console.error("Performance fetch error:", err);
    }
    return null;
  };

  return (
    <AppShell>
      <div className="w-full max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Create Campaign with Demo Data
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300 mb-6">
            See how to create a targeted campaign using sample data and segments. Choose from different demo scenarios below.
          </p>

          {/* Demo Campaign Selector */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {Object.values(demoCampaigns).map((demo) => (
              <button
                key={demo.id}
                onClick={() => {
                  setSelectedDemo(demo.id);
                  setCampaign(null);
                  setAnalysis(null);
                  setStep("segments");
                  setError(null);
                }}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  selectedDemo === demo.id
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md"
                    : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-blue-300 dark:hover:border-blue-700"
                }`}
              >
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-1">{demo.name}</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-2">{demo.description}</p>
                <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-500">
                  <span className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded">
                    {demo.selectedSegments.length} segments
                  </span>
                  <span className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded">
                    {demo.products.length} products
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Step Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[
              { id: "segments", label: "Segments" },
              { id: "create", label: "Create" },
              { id: "analyze", label: "Analyze" },
              { id: "complete", label: "Complete" },
            ].map((s, idx) => {
              const stepIndex = ["segments", "create", "analyze", "complete"].indexOf(step);
              const isActive = s.id === step;
              const isCompleted = ["segments", "create", "analyze", "complete"].indexOf(s.id) < stepIndex;

              return (
                <div key={s.id} className="flex-1 flex items-center">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                        isActive
                          ? "bg-blue-600 text-white"
                          : isCompleted
                          ? "bg-green-500 text-white"
                          : "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                      }`}
                    >
                      {isCompleted ? "✓" : idx + 1}
                    </div>
                    <p className="mt-2 text-xs font-medium text-slate-600 dark:text-slate-400">{s.label}</p>
                  </div>
                  {idx < 3 && (
                    <div
                      className={`flex-1 h-1 mx-2 ${
                        isCompleted ? "bg-green-500" : "bg-slate-200 dark:bg-slate-700"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Campaign Details */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Demo Campaign Details</h2>
            <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm font-medium">
              {demoCampaign.name}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Campaign Name
              </label>
              <div className="px-4 py-2 bg-slate-50 dark:bg-slate-700 rounded-lg text-slate-900 dark:text-slate-100">
                {demoCampaign.campaignName}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Channel</label>
              <div className="px-4 py-2 bg-slate-50 dark:bg-slate-700 rounded-lg text-slate-900 dark:text-slate-100">
                {demoCampaign.channel}
              </div>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Objective</label>
              <div className="px-4 py-2 bg-slate-50 dark:bg-slate-700 rounded-lg text-slate-900 dark:text-slate-100">
                {demoCampaign.objective}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Target Segments
              </label>
              <div className="px-4 py-2 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <div className="flex flex-wrap gap-2">
                    {demoCampaign.selectedSegments.map((seg, idx) => {
                      const segmentName = segments.find(s => s.segment_id === seg)?.name || seg.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
                      return (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm"
                        >
                          {segmentName}
                        </span>
                      );
                    })}
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Products</label>
              <div className="px-4 py-2 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <div className="flex flex-wrap gap-2">
                  {demoCampaign.products.map((prod, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full text-sm"
                    >
                      {prod}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Product Images */}
          {demoCampaign.productImages && demoCampaign.productImages.length > 0 && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                Product Images
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {demoCampaign.productImages.map((img, idx) => (
                  <div key={idx} className="relative group">
                    <img
                      src={img.image_url}
                      alt={img.alt_text || `Product ${idx + 1}`}
                      className="w-full h-32 object-cover rounded-lg border border-slate-200 dark:border-slate-700"
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs p-2 rounded-b-lg">
                      <p className="font-semibold">{img.product_id}</p>
                      {img.alt_text && <p className="text-xs opacity-90">{img.alt_text}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Available Segments */}
        {step === "segments" && (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm mb-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">Available Audience Segments</h2>
            {segments.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {segments.map((segment, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border ${
                      demoCampaign.selectedSegments.includes(segment.segment_id)
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                        : "border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
                    }`}
                  >
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100">{segment.name}</h3>
                    {segment.description && (
                      <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">{segment.description}</p>
                    )}
                    {segment.size && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                        {segment.size.toLocaleString()} customers
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-600 dark:text-slate-300">Loading segments...</p>
            )}
            <div className="mt-6">
              <button
                onClick={() => {
                  setStep("create");
                  createDemoCampaign();
                }}
                disabled={isLoading}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isLoading ? "Creating Campaign..." : "Create Campaign with Demo Data"}
              </button>
            </div>
          </div>
        )}

        {/* Campaign Created */}
        {campaign && step !== "segments" && (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm mb-6">
            <div className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg mb-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="font-semibold text-green-900 dark:text-green-100">Campaign Created Successfully!</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-green-800 dark:text-green-200">
                    <strong>Campaign ID:</strong> {campaign.campaign_id}
                  </p>
                  <p className="text-green-800 dark:text-green-200">
                    <strong>Campaign Name:</strong> {campaign.campaign_name}
                  </p>
                </div>
                <div>
                  <p className="text-green-800 dark:text-green-200">
                    <strong>Estimated Reach:</strong> {campaign.estimated_reach?.toLocaleString()} customers
                  </p>
                  <p className="text-green-800 dark:text-green-200">
                    <strong>Status:</strong> {campaign.status}
                  </p>
                </div>
              </div>
            </div>

            {campaign.segments && campaign.segments.length > 0 && (
              <div className="mb-6">
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">Target Segments</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {campaign.segments.map((seg: any, idx: number) => (
                    <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                      <p className="font-medium text-slate-900 dark:text-slate-100">{seg.name}</p>
                      {seg.description && (
                        <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">{seg.description}</p>
                      )}
                      {seg.size && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {seg.size.toLocaleString()} customers
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {step === "analyze" && (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-blue-800 dark:text-blue-200">Analyzing campaign targeting effectiveness...</p>
              </div>
            )}
          </div>
        )}

        {/* Analysis Results */}
        {analysis && step === "complete" && (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm mb-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">Targeting Analysis Results</h2>

            {analysis.summary && (
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg mb-4">
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">Summary</h4>
                <p className="text-slate-600 dark:text-slate-300">{analysis.summary}</p>
              </div>
            )}

            {analysis.recommendations && analysis.recommendations.length > 0 && (
              <div className="mb-4">
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">Recommendations</h4>
                <ul className="space-y-2">
                  {analysis.recommendations.map((rec: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {analysis.segment_performance && analysis.segment_performance.length > 0 && (
              <div>
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">Segment Performance</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-slate-100 dark:bg-slate-700">
                      <tr>
                        <th className="px-4 py-2 text-left">Segment</th>
                        <th className="px-4 py-2 text-left">Performance</th>
                        <th className="px-4 py-2 text-left">Metrics</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.segment_performance.map((seg: any, idx: number) => (
                        <tr key={idx} className="border-t border-slate-200 dark:border-slate-700">
                          <td className="px-4 py-2 font-medium">{seg.segment_name || seg.segment_id}</td>
                          <td className="px-4 py-2">{seg.performance_score || "N/A"}</td>
                          <td className="px-4 py-2">
                            {seg.metrics ? JSON.stringify(seg.metrics).substring(0, 50) + "..." : "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Link
            href="/campaigns/target"
            className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-center"
          >
            Create Your Own Campaign →
          </Link>
          <Link
            href="/workflow/demo"
            className="flex-1 px-6 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-center"
          >
            Back to Workflow Demo
          </Link>
        </div>
      </div>
    </AppShell>
  );
}

