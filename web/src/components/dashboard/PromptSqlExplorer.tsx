'use client';
import { useCallback, useEffect, useState } from "react";

import { searchCampaigns, listCollections, type VectorSearchResponse, type CampaignSearchResult } from "@/lib/api";

const defaultPrompt = "high performing email campaigns with high conversion rates";

export function PromptSqlExplorer() {
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VectorSearchResponse | null>(null);
  const [collectionName, setCollectionName] = useState("");
  const [numResults, setNumResults] = useState(10);
  const [showAll, setShowAll] = useState(false);
  const [availableCollections, setAvailableCollections] = useState<string[]>([]);
  const [loadingCollections, setLoadingCollections] = useState(true);
  const [expandedCampaigns, setExpandedCampaigns] = useState<Set<string>>(new Set());

  const runQuery = useCallback(
    async (promptValue: string, showAllDocs: boolean = false) => {
      setIsLoading(true);
      setError(null);
      try {
        const payload = await searchCampaigns({
          query: showAllDocs ? "" : promptValue,
          collection_name: collectionName.trim() || undefined,
          num_results: numResults,
          show_all: showAllDocs,
        });
        setResult(payload);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to search campaigns.");
      } finally {
        setIsLoading(false);
      }
    },
    [collectionName, numResults],
  );

  useEffect(() => {
    // Load available collections
    const loadCollections = async () => {
      try {
        setLoadingCollections(true);
        const collections = await listCollections();
        setAvailableCollections(collections);
        if (collections.length > 0 && !collectionName) {
          // Set default to first collection or "klaviyo_campaigns" if available
          const defaultCollection = collections.find(c => c === "UCO_Gear_Campaigns") || collections[0];
          setCollectionName(defaultCollection);
        }
      } catch (err) {
        console.error("Failed to load collections:", err);
      } finally {
        setLoadingCollections(false);
      }
    };
    
    loadCollections();
  }, []);

  useEffect(() => {
    if (!loadingCollections && !showAll) {
      runQuery(defaultPrompt);
    }
  }, [loadingCollections]);
  
  const toggleExpanded = (campaignId: string) => {
    setExpandedCampaigns(prev => {
      const next = new Set(prev);
      if (next.has(campaignId)) {
        next.delete(campaignId);
      } else {
        next.add(campaignId);
      }
      return next;
    });
  };

  const formatCampaignData = (campaign: CampaignSearchResult) => {
    const analysis = campaign.analysis || {};
    const metadata = campaign.metadata || {};
    
    return {
      campaign_id: campaign.campaign_id,
      campaign_name: analysis.campaign_name || metadata.campaign_name || campaign.campaign_id,
      similarity_score: (campaign.similarity_score * 100).toFixed(1) + "%",
      subject: analysis.subject || metadata.subject || "N/A",
      products: analysis.products || metadata.products || [],
      metrics: analysis.metrics || metadata.metrics || {},
      visual_elements: analysis.visual_elements || [],
      colors: analysis.dominant_colors || metadata.dominant_colors || [],
    };
  };

  return (
    <div className="flex h-full flex-col gap-6">
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Vector Database Explorer</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Search campaigns in the vector database using natural language queries.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <label className="flex flex-col gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Search Query</span>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="min-h-[120px] w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 focus:border-slate-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-slate-500"
              placeholder="e.g., high performing email campaigns with high conversion rates"
            />
          </label>
          <div className="flex flex-col gap-3">
            <label className="flex flex-col gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Collection</span>
              <select
                value={collectionName}
                onChange={(e) => setCollectionName(e.target.value)}
                className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-700 focus:border-slate-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-slate-500"
                disabled={loadingCollections}
              >
                {loadingCollections ? (
                  <option>Loading collections...</option>
                ) : availableCollections.length > 0 ? (
                  <>
                    <option value="">All Collections (default)</option>
                    {availableCollections.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </>
                ) : (
                  <option value="">No collections found</option>
                )}
              </select>
              {!loadingCollections && availableCollections.length > 0 && (
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {availableCollections.length} collection{availableCollections.length !== 1 ? 's' : ''} available
                </p>
              )}
            </label>
            <label className="flex flex-col gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Number of Results</span>
              <input
                type="number"
                min={1}
                max={50}
                value={numResults}
                onChange={(e) => setNumResults(parseInt(e.target.value) || 10)}
                className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-700 focus:border-slate-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-slate-500"
              />
            </label>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => runQuery(prompt, false)}
            className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200 dark:disabled:bg-slate-600"
            disabled={isLoading || (!prompt.trim() && !showAll)}
          >
            {isLoading ? "Searching..." : "Search Campaigns"}
          </button>
          <button
            onClick={() => {
              setShowAll(true);
              runQuery("", true);
            }}
            className="rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400 dark:bg-blue-500 dark:hover:bg-blue-600"
            disabled={isLoading}
          >
            {isLoading ? "Loading..." : "Show All Documents"}
          </button>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showAll}
              onChange={(e) => {
                setShowAll(e.target.checked);
                if (e.target.checked) {
                  runQuery("", true);
                } else {
                  runQuery(prompt, false);
                }
              }}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-xs text-slate-600 dark:text-slate-400">Show all documents</span>
          </label>
          {result ? (
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Found <span className="text-slate-700 dark:text-slate-300">{result.total_found}</span> campaigns
            </p>
          ) : null}
          {error ? <p className="text-xs font-medium text-rose-600 dark:text-rose-400">{error}</p> : null}
        </div>
      </div>

      {result && result.campaigns.length > 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
          <div className="mb-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Search Results for: "{result.query}"
            </p>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Found {result.total_found} campaign{result.total_found !== 1 ? 's' : ''} matching your query
            </p>
          </div>
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {result.campaigns.map((campaign, idx) => {
              const data = formatCampaignData(campaign);
              const isExpanded = expandedCampaigns.has(campaign.campaign_id);
              const hasFullData = campaign.document || (campaign.analysis && typeof campaign.analysis === 'object');
              
              return (
                <div
                  key={campaign.campaign_id}
                  className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-700/50"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {data.campaign_name}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-1">
                        ID: {data.campaign_id}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {data.similarity_score !== "100.0%" && (
                        <div className="text-xs font-medium text-slate-600 dark:text-slate-300 bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded">
                          {data.similarity_score} match
                        </div>
                      )}
                      {hasFullData && (
                        <button
                          onClick={() => toggleExpanded(campaign.campaign_id)}
                          className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline px-2 py-1"
                        >
                          {isExpanded ? "Hide" : "Show"} Full Data
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {data.subject && data.subject !== "N/A" && (
                    <div className="mt-2">
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Subject: </span>
                      <span className="text-xs text-slate-700 dark:text-slate-300">{data.subject}</span>
                    </div>
                  )}
                  
                  {data.products && Array.isArray(data.products) && data.products.length > 0 && (
                    <div className="mt-2">
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Products: </span>
                      <span className="text-xs text-slate-700 dark:text-slate-300">
                        {data.products.slice(0, 5).join(", ")}
                        {data.products.length > 5 && ` +${data.products.length - 5} more`}
                      </span>
                    </div>
                  )}
                  
                  {data.metrics && Object.keys(data.metrics).length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {data.metrics.open_rate && (
                        <span className="text-xs text-slate-600 dark:text-slate-400">
                          Open: {((data.metrics.open_rate || 0) * 100).toFixed(1)}%
                        </span>
                      )}
                      {data.metrics.conversion_rate && (
                        <span className="text-xs text-slate-600 dark:text-slate-400">
                          Conversion: {((data.metrics.conversion_rate || 0) * 100).toFixed(1)}%
                        </span>
                      )}
                      {data.metrics.revenue && (
                        <span className="text-xs text-slate-600 dark:text-slate-400">
                          Revenue: ${(data.metrics.revenue || 0).toFixed(2)}
                        </span>
                      )}
                    </div>
                  )}
                  
                  {data.colors && data.colors.length > 0 && (
                    <div className="mt-2">
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Colors: </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {data.colors.slice(0, 5).map((color: string, cidx: number) => (
                          <span
                            key={cidx}
                            className="rounded px-2 py-0.5 text-xs bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-300"
                          >
                            {color}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Full Document Data */}
                  {isExpanded && hasFullData && (
                    <div className="mt-4 pt-4 border-t border-slate-300 dark:border-slate-600">
                      <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">Full Document Data</h4>
                      
                      {/* Metadata */}
                      {campaign.metadata && Object.keys(campaign.metadata).length > 0 && (
                        <div className="mb-3">
                          <h5 className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Metadata:</h5>
                          <pre className="text-xs bg-slate-100 dark:bg-slate-800 p-2 rounded overflow-x-auto max-h-40 overflow-y-auto">
                            {JSON.stringify(campaign.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                      
                      {/* Analysis */}
                      {campaign.analysis && (
                        <div className="mb-3">
                          <h5 className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Analysis:</h5>
                          <pre className="text-xs bg-slate-100 dark:bg-slate-800 p-2 rounded overflow-x-auto max-h-60 overflow-y-auto">
                            {typeof campaign.analysis === 'string' 
                              ? campaign.analysis 
                              : JSON.stringify(campaign.analysis, null, 2)}
                          </pre>
                        </div>
                      )}
                      
                      {/* Raw Document */}
                      {campaign.document && (
                        <div className="mb-3">
                          <h5 className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Raw Document:</h5>
                          <pre className="text-xs bg-slate-100 dark:bg-slate-800 p-2 rounded overflow-x-auto max-h-60 overflow-y-auto">
                            {typeof campaign.document === 'string' 
                              ? campaign.document 
                              : JSON.stringify(campaign.document, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : result && result.campaigns.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            No campaigns found matching your query. Try a different search term.
          </p>
        </div>
      ) : null}
    </div>
  );
}
