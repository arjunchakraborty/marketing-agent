"use client";

import { useState, useEffect } from "react";
import {
  getCampaignSegments,
  createTargetedCampaign,
  analyzeTargeting,
} from "@/lib/api";
import { ProductImageUploader } from "./ProductImageUploader";

interface ProductImage {
  product_id: string;
  image_url: string;
  alt_text?: string;
}

export function TargetCampaignBuilder() {
  const [segments, setSegments] = useState<any[]>([]);
  const [selectedSegments, setSelectedSegments] = useState<string[]>([]);
  const [campaignName, setCampaignName] = useState("");
  const [objective, setObjective] = useState("increase_revenue");
  const [channel, setChannel] = useState("email");
  const [products, setProducts] = useState<string[]>([]);
  const [productImages, setProductImages] = useState<ProductImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSegments();
  }, []);

  const loadSegments = async () => {
    try {
      const data = await getCampaignSegments();
      setSegments(data.segments);
    } catch (err: any) {
      setError(err.message || "Failed to load segments");
    }
  };

  const handleSegmentToggle = (segmentId: string) => {
    setSelectedSegments((prev) =>
      prev.includes(segmentId)
        ? prev.filter((id) => id !== segmentId)
        : [...prev, segmentId]
    );
  };

  const handleCreateCampaign = async () => {
    if (!campaignName || selectedSegments.length === 0) {
      setError("Please provide a campaign name and select at least one segment");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const campaign = await createTargetedCampaign({
        campaign_name: campaignName,
        segment_ids: selectedSegments,
        channel,
        objective,
        products: products.length > 0 ? products : undefined,
        product_images: productImages.length > 0 ? productImages : undefined,
      });
      setResult(campaign);
    } catch (err: any) {
      setError(err.message || "Failed to create campaign");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (selectedSegments.length === 0) {
      setError("Please select at least one segment to analyze");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const analysis = await analyzeTargeting({
        segment_ids: selectedSegments,
      });
      setResult(analysis);
    } catch (err: any) {
      setError(err.message || "Failed to analyze targeting");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="campaign-name" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Campaign Name *
          </label>
          <input
            id="campaign-name"
            type="text"
            value={campaignName}
            onChange={(e) => setCampaignName(e.target.value)}
            placeholder="Enter campaign name"
            className="w-full min-h-[44px] px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label htmlFor="channel" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Channel
            </label>
            <select
              id="channel"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="w-full min-h-[44px] px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="email">Email</option>
              <option value="sms">SMS</option>
              <option value="push">Push Notification</option>
            </select>
          </div>

          <div className="space-y-2">
            <label htmlFor="objective" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Objective
            </label>
            <select
              id="objective"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full min-h-[44px] px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="increase_revenue">Increase Revenue</option>
              <option value="acquire_customers">Acquire Customers</option>
              <option value="retain_customers">Retain Customers</option>
              <option value="promote_product">Promote Product</option>
            </select>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="products" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Products (comma-separated)
          </label>
          <input
            id="products"
            type="text"
            value={products.join(", ")}
            onChange={(e) => setProducts(e.target.value.split(",").map((p) => p.trim()).filter(Boolean))}
            placeholder="PROD001, PROD002, PROD003"
            className="w-full min-h-[44px] px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <ProductImageUploader
          products={products}
          onImagesChange={setProductImages}
          initialImages={productImages}
        />
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Select Audience Segments *
        </h3>
        <div className="space-y-3">
          {segments.map((segment) => (
            <label
              key={segment.segment_id}
              className="flex items-start gap-3 p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50"
            >
              <input
                type="checkbox"
                checked={selectedSegments.includes(segment.segment_id)}
                onChange={() => handleSegmentToggle(segment.segment_id)}
                className="mt-1 min-w-[20px] min-h-[20px]"
              />
              <div className="flex-1">
                <div className="font-semibold text-slate-900 dark:text-slate-100">
                  {segment.name}
                </div>
                {segment.description && (
                  <div className="text-sm text-slate-600 dark:text-slate-300 mt-1">
                    {segment.description}
                  </div>
                )}
                {segment.size && (
                  <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Estimated size: {segment.size.toLocaleString()} customers
                  </div>
                )}
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <button
          onClick={handleCreateCampaign}
          disabled={loading || !campaignName || selectedSegments.length === 0}
          className="flex-1 min-h-[44px] px-6 py-3 bg-slate-900 text-white rounded-lg font-semibold hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Creating..." : "Create Campaign"}
        </button>
        <button
          onClick={handleAnalyze}
          disabled={loading || selectedSegments.length === 0}
          className="flex-1 min-h-[44px] px-6 py-3 border-2 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100 rounded-lg font-semibold hover:border-slate-400 dark:hover:border-slate-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Analyzing..." : "Analyze Targeting"}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {result && (
        <div className="p-4 md:p-6 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
          <h3 className="text-lg font-semibold text-green-800 dark:text-green-200 mb-3">
            {result.campaign_id ? "Campaign Created!" : "Analysis Results"}
          </h3>
          <div className="space-y-2 text-sm text-green-700 dark:text-green-300">
            {result.campaign_id && (
              <>
                <p>
                  <span className="font-semibold">Campaign ID:</span> {result.campaign_id}
                </p>
                <p>
                  <span className="font-semibold">Estimated Reach:</span>{" "}
                  {result.estimated_reach?.toLocaleString()} customers
                </p>
              </>
            )}
            {result.recommendations && (
              <div>
                <p className="font-semibold mb-2">Recommendations:</p>
                <ul className="list-disc list-inside space-y-1">
                  {result.recommendations.map((rec: string, idx: number) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.summary && (
              <p>
                <span className="font-semibold">Summary:</span> {result.summary}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

