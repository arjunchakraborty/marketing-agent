"use client";

import { useEffect, useState, useRef } from "react";
import { listExperiments, generateEmailCampaign, getProductsFromVector, prepareCampaignHtmlForPreview, type ExperimentResultsResponse, type EmailCampaignGenerationRequest, type EmailCampaignResponse } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogFooter } from "@/components/ui/dialog";

interface ExperimentSummary {
  experiment_run_id: string;
  name: string | null;
  created_at: string | null;
  status: string;
  campaigns_analyzed: number;
  key_features?: string[];
  patterns?: {
    visual?: string;
    messaging?: string;
    design?: string;
  };
  recommendations?: string[];
  hero_image_prompts?: string[];
  text_prompts?: string[];
  call_to_action_prompts?: string[];
  summary?: string;
  prompt_query?: string;
}

export function RecommendationBoard() {
  const [experiments, setExperiments] = useState<ExperimentResultsResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedExperiment, setExpandedExperiment] = useState<string | null>(null);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [generationResult, setGenerationResult] = useState<any>(null);
  const [emailPreviewOpen, setEmailPreviewOpen] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState<ExperimentSummary | null>(null);
  const [availableProducts, setAvailableProducts] = useState<string[]>([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [productsDropdownOpen, setProductsDropdownOpen] = useState(false);
  const [productSearchQuery, setProductSearchQuery] = useState("");
  const productSearchInputRef = useRef<HTMLInputElement>(null);
  const productsDropdownRef = useRef<HTMLDivElement>(null);

  const [formData, setFormData] = useState<EmailCampaignGenerationRequest>({
    objective: "",
    products: [],
    key_message: "",
    design_guidance: "",
    tone: "professional",
    use_past_campaigns: true,
    num_similar_campaigns: 5,
    subject_line_suggestions: 3,
    include_preview_text: true,
  });

  useEffect(() => {
    loadExperiments();
  }, []);

  useEffect(() => {
    if (!productsDropdownOpen) {
      setProductSearchQuery("");
      return;
    }
    const handleClickOutside = (e: MouseEvent) => {
      if (productsDropdownRef.current && !productsDropdownRef.current.contains(e.target as Node)) {
        setProductsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [productsDropdownOpen]);

  useEffect(() => {
    if (productsDropdownOpen && availableProducts.length > 0) {
      const t = setTimeout(() => productSearchInputRef.current?.focus(), 0);
      return () => clearTimeout(t);
    }
  }, [productsDropdownOpen, availableProducts.length]);

  useEffect(() => {
    if (!generateDialogOpen) return;
    let cancelled = false;
    setProductsLoading(true);
    setAvailableProducts([]);
    getProductsFromVector()
      .then((res) => {
        if (cancelled) return;
        const names = (res.products || []).map((p) => p.product_name).filter(Boolean);
        setAvailableProducts(names);
      })
      .catch(() => {
        if (!cancelled) setAvailableProducts([]);
      })
      .finally(() => {
        if (!cancelled) setProductsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [generateDialogOpen]);

  const loadExperiments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listExperiments();
      const sorted = data.sort((a, b) => {
        const dateA = a.experiment_run.created_at ? new Date(a.experiment_run.created_at).getTime() : 0;
        const dateB = b.experiment_run.created_at ? new Date(b.experiment_run.created_at).getTime() : 0;
        return dateB - dateA;
      });
      setExperiments(sorted);
    } catch (err: any) {
      setError(err.message || "Failed to load experiments");
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptAndGenerate = (experimentId: string, summary: ExperimentSummary) => {
    setSelectedExperimentId(experimentId);
    setSelectedSummary(summary);

    // Build design guidance from visual + design patterns only
    const designParts: string[] = [];
    if (summary.patterns?.visual) designParts.push(`Visual: ${summary.patterns.visual}`);
    if (summary.patterns?.design) designParts.push(`Design: ${summary.patterns.design}`);
    const designGuidance = designParts.join("\n");

    // key_message = text prompts, design_guidance = visual + design patterns
    const textPrompts = (summary.text_prompts || []).join("\n");

    setFormData({
      objective: "",
      products: [],
      key_message: textPrompts,
      design_guidance: designGuidance,
      tone: "professional",
      use_past_campaigns: true,
      num_similar_campaigns: 5,
      subject_line_suggestions: 3,
      include_preview_text: true,
    });
    setGenerationError(null);
    setGenerationResult(null);
    setGenerateDialogOpen(true);
  };

  const handleGenerateCampaigns = async () => {
    const fromExperiment = Boolean(selectedExperimentId);
    if (!fromExperiment) {
      if (!formData.objective || !formData.objective.trim()) {
        setGenerationError("Campaign objective is required");
        return;
      }
      if (!formData.products || formData.products.length === 0) {
        setGenerationError("Please select at least one product");
        return;
      }
    }

    setGenerating(true);
    setGenerationError(null);
    setGenerationResult(null);

    try {
      let request = fromExperiment
        ? { ...formData, experiment_run_id: selectedExperimentId!, objective: formData.objective || "Generate from experiment" }
        : { ...formData };

      // Include experiment prompts in the request
      if (selectedSummary) {
        if (selectedSummary.hero_image_prompts && selectedSummary.hero_image_prompts.length > 0) {
          request.hero_image_prompt = selectedSummary.hero_image_prompts.join("\n");
          request.generate_hero_image = true;
        }
        if (selectedSummary.call_to_action_prompts && selectedSummary.call_to_action_prompts.length > 0) {
          request.call_to_action = selectedSummary.call_to_action_prompts.join(" | ");
        }
        if (selectedSummary.text_prompts && selectedSummary.text_prompts.length > 0 && !request.key_message) {
          request.key_message = selectedSummary.text_prompts.join("\n");
        }
      }

      const result = await generateEmailCampaign(request);
      setGenerationResult(result);
    } catch (err: any) {
      setGenerationError(err.message || "Failed to generate campaign");
    } finally {
      setGenerating(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Unknown date";
    try {
      const date = new Date(dateString);
      return date.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400";
      case "failed":
      case "error":
        return "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400";
      case "running":
        return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";
      default:
        return "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300";
    }
  };

  const extractExperimentSummary = (exp: ExperimentResultsResponse): ExperimentSummary => {
    const resultsSummary = exp.experiment_run.results_summary || {};
    const config = exp.experiment_run.config || {};
    
    return {
      experiment_run_id: exp.experiment_run.experiment_run_id,
      name: exp.experiment_run.name,
      created_at: exp.experiment_run.created_at,
      status: exp.experiment_run.status,
      campaigns_analyzed: resultsSummary.campaigns_analyzed || exp.campaign_analyses.length || 0,
      key_features: Array.isArray(resultsSummary.key_features) ? resultsSummary.key_features : undefined,
      patterns: resultsSummary.patterns && typeof resultsSummary.patterns === 'object' ? resultsSummary.patterns : undefined,
      recommendations: Array.isArray(resultsSummary.recommendations) ? resultsSummary.recommendations : undefined,
      // Use direct fields from API response if available, otherwise fall back to results_summary
      hero_image_prompts: Array.isArray(exp.hero_image_prompts) ? exp.hero_image_prompts : 
                          (Array.isArray(resultsSummary.hero_image_prompts) ? resultsSummary.hero_image_prompts : undefined),
      text_prompts: Array.isArray(exp.text_prompts) ? exp.text_prompts :
                    (Array.isArray(resultsSummary.text_prompts) ? resultsSummary.text_prompts : undefined),
      call_to_action_prompts: Array.isArray(exp.call_to_action_prompts) ? exp.call_to_action_prompts :
                              (Array.isArray(resultsSummary.call_to_action_prompts) ? resultsSummary.call_to_action_prompts : undefined),
      summary: typeof resultsSummary.summary === 'string' ? resultsSummary.summary : undefined,
      prompt_query: config.prompt_query || resultsSummary.prompt_query || undefined,
    };
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Experiment History</CardTitle>
          <CardDescription>Loading experiments...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-500 dark:text-slate-400">
            Loading experiment history...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Experiment History</CardTitle>
          <CardDescription>Failed to load experiments</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-300">
            {error}
          </div>
          <Button onClick={loadExperiments} className="mt-4" variant="outline">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (experiments.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Experiment History</CardTitle>
          <CardDescription>No experiments found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-500 dark:text-slate-400">
            Run your first experiment to see results here.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Experiment History</CardTitle>
            <CardDescription>
              Campaign analysis experiments sorted by most recent
            </CardDescription>
          </div>
          <Button onClick={loadExperiments} variant="outline" size="sm">
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {experiments.map((exp) => {
            const summary = extractExperimentSummary(exp);
            const isExpanded = expandedExperiment === summary.experiment_run_id;

            return (
              <div
                key={summary.experiment_run_id}
                className="rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 transition-all hover:shadow-md"
              >
                <div
                  className="p-4 cursor-pointer"
                  onClick={() => setExpandedExperiment(isExpanded ? null : summary.experiment_run_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="text-base font-semibold text-slate-800 dark:text-slate-100">
                          {summary.name || `Experiment ${summary.experiment_run_id.substring(0, 8)}`}
                        </h4>
                        <Badge className={getStatusColor(summary.status)}>
                          {summary.status.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="mb-2">
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                          <span className="font-semibold">ID:</span> {summary.experiment_run_id}
                        </p>
                      </div>
                      {summary.prompt_query && (
                        <p className="text-sm text-slate-600 dark:text-slate-300 mb-2">
                          <span className="font-semibold">Query:</span> {summary.prompt_query}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                        <span>{formatDate(summary.created_at)}</span>
                        <span>•</span>
                        <span>{summary.campaigns_analyzed} campaigns analyzed</span>
                        {summary.key_features && summary.key_features.length > 0 && (
                          <>
                            <span>•</span>
                            <span>{summary.key_features.length} key features</span>
                          </>
                        )}
                        {((summary.recommendations && summary.recommendations.length > 0) ||
                          (summary.hero_image_prompts && summary.hero_image_prompts.length > 0) ||
                          (summary.text_prompts && summary.text_prompts.length > 0) ||
                          (summary.call_to_action_prompts && summary.call_to_action_prompts.length > 0)) && (
                          <>
                            <span>•</span>
                            <span>
                              {(summary.recommendations?.length || 0) +
                               (summary.hero_image_prompts?.length || 0) +
                               (summary.text_prompts?.length || 0) +
                               (summary.call_to_action_prompts?.length || 0)} recommendations
                            </span>
                          </>
                        )}
                      </div>
                      {/* Show prompt previews when collapsed */}
                      {!isExpanded && (
                        <div className="mt-3 space-y-2">
                          {summary.hero_image_prompts && summary.hero_image_prompts.length > 0 && (
                            <div className="text-xs">
                              <span className="font-semibold text-slate-700 dark:text-slate-300">Hero Image Prompts:</span>
                              <div className="mt-1 space-y-1">
                                {summary.hero_image_prompts.slice(0, 2).map((prompt, idx) => (
                                  <div key={idx} className="text-slate-600 dark:text-slate-400 italic pl-2">
                                    "{prompt}"
                                  </div>
                                ))}
                                {summary.hero_image_prompts.length > 2 && (
                                  <div className="text-slate-500 dark:text-slate-500">
                                    +{summary.hero_image_prompts.length - 2} more
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                          {summary.text_prompts && summary.text_prompts.length > 0 && (
                            <div className="text-xs">
                              <span className="font-semibold text-slate-700 dark:text-slate-300">Text Prompts:</span>
                              <div className="mt-1 space-y-1">
                                {summary.text_prompts.slice(0, 2).map((prompt, idx) => (
                                  <div key={idx} className="text-slate-600 dark:text-slate-400 italic pl-2">
                                    "{prompt}"
                                  </div>
                                ))}
                                {summary.text_prompts.length > 2 && (
                                  <div className="text-slate-500 dark:text-slate-500">
                                    +{summary.text_prompts.length - 2} more
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                          {summary.call_to_action_prompts && summary.call_to_action_prompts.length > 0 && (
                            <div className="text-xs">
                              <span className="font-semibold text-slate-700 dark:text-slate-300">Call to Action Prompts:</span>
                              <div className="mt-1 space-y-1">
                                {summary.call_to_action_prompts.slice(0, 2).map((prompt, idx) => (
                                  <div key={idx} className="text-slate-600 dark:text-slate-400 italic pl-2">
                                    "{prompt}"
                                  </div>
                                ))}
                                {summary.call_to_action_prompts.length > 2 && (
                                  <div className="text-slate-500 dark:text-slate-500">
                                    +{summary.call_to_action_prompts.length - 2} more
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Button variant="ghost" size="sm" onClick={() => setExpandedExperiment(isExpanded ? null : summary.experiment_run_id)}>
                        {isExpanded ? "Hide" : "Show Details"}
                      </Button>
                      {((summary.recommendations && summary.recommendations.length > 0) ||
                        (summary.hero_image_prompts && summary.hero_image_prompts.length > 0) ||
                        (summary.text_prompts && summary.text_prompts.length > 0) ||
                        (summary.call_to_action_prompts && summary.call_to_action_prompts.length > 0)) && (
                        <Button
                          variant="default"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAcceptAndGenerate(summary.experiment_run_id, summary);
                          }}
                        >
                          Accept & Generate
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {isExpanded && (
                  <div className="border-t border-slate-200 dark:border-slate-700 p-4 bg-slate-50 dark:bg-slate-900/50">
                    <Tabs defaultValue="features" className="w-full">
                      <TabsList>
                        <TabsTrigger value="features">
                          Key Features ({summary.key_features?.length || 0})
                        </TabsTrigger>
                        <TabsTrigger value="patterns">Patterns</TabsTrigger>
                        <TabsTrigger value="recommendations">
                          Recommendations ({
                            (summary.recommendations?.length || 0) +
                            (summary.hero_image_prompts?.length || 0) +
                            (summary.text_prompts?.length || 0) +
                            (summary.call_to_action_prompts?.length || 0)
                          })
                        </TabsTrigger>
                        <TabsTrigger value="campaigns">
                          Campaigns ({exp.campaign_analyses.length})
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="features" className="mt-4">
                        {summary.summary && (
                          <div className="mb-4 p-3 rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                            <p className="text-sm text-blue-800 dark:text-blue-200">
                              {summary.summary}
                            </p>
                          </div>
                        )}
                        {summary.key_features && summary.key_features.length > 0 ? (
                          <ul className="list-disc list-inside space-y-2 text-sm text-slate-600 dark:text-slate-300">
                            {summary.key_features.map((feature, idx) => (
                              <li key={idx}>{feature}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-slate-500 dark:text-slate-400">No key features available</p>
                        )}
                      </TabsContent>

                      <TabsContent value="patterns" className="mt-4">
                        {summary.patterns && Object.keys(summary.patterns).length > 0 ? (
                          <div className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
                            {summary.patterns.visual && (
                              <div>
                                <span className="font-semibold text-slate-800 dark:text-slate-100">Visual Patterns: </span>
                                <span>{summary.patterns.visual}</span>
                              </div>
                            )}
                            {summary.patterns.messaging && (
                              <div>
                                <span className="font-semibold text-slate-800 dark:text-slate-100">Messaging Patterns: </span>
                                <span>{summary.patterns.messaging}</span>
                              </div>
                            )}
                            {summary.patterns.design && (
                              <div>
                                <span className="font-semibold text-slate-800 dark:text-slate-100">Design Patterns: </span>
                                <span>{summary.patterns.design}</span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500 dark:text-slate-400">No patterns available</p>
                        )}
                      </TabsContent>

                      <TabsContent value="recommendations" className="mt-4">
                        {(summary.recommendations && summary.recommendations.length > 0) ||
                         (summary.hero_image_prompts && summary.hero_image_prompts.length > 0) ||
                         (summary.text_prompts && summary.text_prompts.length > 0) ||
                         (summary.call_to_action_prompts && summary.call_to_action_prompts.length > 0) ? (
                          <div className="space-y-6">
                            {summary.hero_image_prompts && summary.hero_image_prompts.length > 0 && (
                              <div>
                                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-2">
                                  Hero Image Prompts ({summary.hero_image_prompts.length})
                                </h4>
                                <ul className="list-disc list-inside space-y-2 text-sm text-slate-600 dark:text-slate-300">
                                  {summary.hero_image_prompts.map((prompt, idx) => (
                                    <li key={idx} className="pl-2">{prompt}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {summary.text_prompts && summary.text_prompts.length > 0 && (
                              <div>
                                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-2">
                                  Text Prompts ({summary.text_prompts.length})
                                </h4>
                                <ul className="list-disc list-inside space-y-2 text-sm text-slate-600 dark:text-slate-300">
                                  {summary.text_prompts.map((prompt, idx) => (
                                    <li key={idx} className="pl-2">{prompt}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {summary.call_to_action_prompts && summary.call_to_action_prompts.length > 0 && (
                              <div>
                                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-2">
                                  Call to Action Prompts ({summary.call_to_action_prompts.length})
                                </h4>
                                <ul className="list-disc list-inside space-y-2 text-sm text-slate-600 dark:text-slate-300">
                                  {summary.call_to_action_prompts.map((prompt, idx) => (
                                    <li key={idx} className="pl-2">{prompt}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {summary.recommendations && summary.recommendations.length > 0 && (
                              <div>
                                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-2">
                                  General Recommendations ({summary.recommendations.length})
                                </h4>
                                <ul className="list-disc list-inside space-y-2 text-sm text-slate-600 dark:text-slate-300">
                                  {summary.recommendations.map((rec, idx) => (
                                    <li key={idx} className="pl-2">{rec}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500 dark:text-slate-400">No recommendations available</p>
                        )}
                      </TabsContent>

                      <TabsContent value="campaigns" className="mt-4">
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {exp.campaign_analyses.length > 0 ? (
                            exp.campaign_analyses.map((campaign, idx) => (
                              <div
                                key={idx}
                                className="rounded border border-slate-200 dark:border-slate-700 p-3 text-sm dark:bg-slate-800"
                              >
                                <div className="font-semibold dark:text-slate-100">
                                  {campaign.campaign_name || campaign.campaign_id || `Campaign ${idx + 1}`}
                                </div>
                                {campaign.metrics && (
                                  <div className="mt-2 text-xs text-slate-600 dark:text-slate-300">
                                    {campaign.metrics.open_rate && (
                                      <span>Open Rate: {((campaign.metrics.open_rate || 0) * 100).toFixed(2)}%</span>
                                    )}
                                    {campaign.metrics.conversion_rate && (
                                      <>
                                        <span className="mx-2">•</span>
                                        <span>Conversion: {((campaign.metrics.conversion_rate || 0) * 100).toFixed(2)}%</span>
                                      </>
                                    )}
                                    {campaign.metrics.revenue && (
                                      <>
                                        <span className="mx-2">•</span>
                                        <span>Revenue: ${(campaign.metrics.revenue || 0).toFixed(2)}</span>
                                      </>
                                    )}
                                  </div>
                                )}
                              </div>
                            ))
                          ) : (
                            <p className="text-sm text-slate-500 dark:text-slate-400">No campaign analyses available</p>
                          )}
                        </div>
                      </TabsContent>
                    </Tabs>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>

      <Dialog
        open={generateDialogOpen}
        onOpenChange={(open) => {
          setGenerateDialogOpen(open);
          if (!open) setEmailPreviewOpen(false);
        }}
        title="Generate Campaigns"
        description="Configure campaign generation based on the selected recommendation"
        contentClassName="max-w-5xl"
      >
        <DialogContent>
          <div className="space-y-4">
            {selectedExperimentId && (
              <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 px-3 py-2">
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  <span className="font-semibold">Experiment:</span>{" "}
                  <span className="font-mono">{selectedExperimentId}</span>
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="campaign-objective">Campaign Objective *</Label>
              <Textarea
                id="campaign-objective"
                value={formData.objective || ""}
                onChange={(e) => setFormData({ ...formData, objective: e.target.value })}
                placeholder="e.g., Increase sales, Promote new product, Re-engage customers"
                rows={2}
                required
              />
            </div>

            {selectedSummary?.hero_image_prompts && selectedSummary.hero_image_prompts.length > 0 && (
              <div className="space-y-1">
                <Label>Hero Image Prompts</Label>
                <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-3 max-h-32 overflow-y-auto">
                  <ul className="space-y-1 text-sm text-slate-700 dark:text-slate-300">
                    {selectedSummary.hero_image_prompts.map((prompt, idx) => (
                      <li key={idx} className="flex gap-2">
                        <span className="text-slate-400 shrink-0">{idx + 1}.</span>
                        <span>{prompt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {selectedSummary?.text_prompts && selectedSummary.text_prompts.length > 0 && (
              <div className="space-y-1">
                <Label>Text Prompts</Label>
                <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-3 max-h-32 overflow-y-auto">
                  <ul className="space-y-1 text-sm text-slate-700 dark:text-slate-300">
                    {selectedSummary.text_prompts.map((prompt, idx) => (
                      <li key={idx} className="flex gap-2">
                        <span className="text-slate-400 shrink-0">{idx + 1}.</span>
                        <span>{prompt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {selectedSummary?.call_to_action_prompts && selectedSummary.call_to_action_prompts.length > 0 && (
              <div className="space-y-1">
                <Label>Call to Action Prompts</Label>
                <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-3 max-h-32 overflow-y-auto">
                  <ul className="space-y-1 text-sm text-slate-700 dark:text-slate-300">
                    {selectedSummary.call_to_action_prompts.map((prompt, idx) => (
                      <li key={idx} className="flex gap-2">
                        <span className="text-slate-400 shrink-0">{idx + 1}.</span>
                        <span>{prompt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="key-message">Key Message</Label>
              <Textarea
                id="key-message"
                value={formData.key_message || ""}
                onChange={(e) => setFormData({ ...formData, key_message: e.target.value })}
                placeholder="Key message or value proposition for the campaign"
                rows={2}
              />
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Pre-filled from text prompts (editable)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="design-guidance">Design Guidance</Label>
              <Textarea
                id="design-guidance"
                value={formData.design_guidance || ""}
                onChange={(e) => setFormData({ ...formData, design_guidance: e.target.value })}
                placeholder="Visual style, design patterns, or layout preferences"
                rows={2}
              />
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Pre-filled from visual and design patterns (editable)
              </p>
            </div>

            <div className="space-y-2" ref={productsDropdownRef}>
              <Label>Select Products</Label>
              {productsLoading ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">Loading products...</p>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => setProductsDropdownOpen((o) => !o)}
                    className="flex w-full items-center justify-between gap-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-left text-sm shadow-sm hover:bg-slate-50 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900"
                  >
                    <span className="text-slate-700 dark:text-slate-300 truncate">
                      {formData.products && formData.products.length > 0
                        ? `${formData.products.length} product${formData.products.length !== 1 ? "s" : ""} selected`
                        : "Choose products..."}
                    </span>
                    <svg
                      className={`h-4 w-4 shrink-0 text-slate-500 transition-transform ${productsDropdownOpen ? "rotate-180" : ""}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {productsDropdownOpen && (
                    <div className="relative z-10 mt-1 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-lg">
                      <div className="sticky top-0 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-2">
                        <Input
                          ref={productSearchInputRef}
                          type="text"
                          value={productSearchQuery}
                          onChange={(e) => setProductSearchQuery(e.target.value)}
                          onKeyDown={(e) => e.stopPropagation()}
                          placeholder="Search products..."
                          className="h-8 text-sm"
                        />
                      </div>
                      <div className="max-h-44 overflow-y-auto">
                        {availableProducts.length === 0 ? (
                          <p className="px-3 py-4 text-sm text-slate-500 dark:text-slate-400">
                            No products available. Upload a product zip (Data Upload → Products) or add sales data to
                            see products here.
                          </p>
                        ) : (() => {
                          const q = productSearchQuery.trim().toLowerCase();
                          const filtered =
                            q === ""
                              ? availableProducts
                              : availableProducts.filter((p) => p.toLowerCase().includes(q));
                          return filtered.length > 0 ? (
                            filtered.map((product) => {
                              const isSelected = formData.products?.includes(product) || false;
                              return (
                                <label
                                  key={product}
                                  className="flex cursor-pointer items-center gap-2 border-b border-slate-100 dark:border-slate-800 px-3 py-2 last:border-b-0 hover:bg-slate-50 dark:hover:bg-slate-800"
                                >
                                  <input
                                    type="checkbox"
                                    checked={isSelected}
                                    onChange={(e) => {
                                      const currentProducts = formData.products || [];
                                      if (e.target.checked) {
                                        setFormData({
                                          ...formData,
                                          products: [...currentProducts, product],
                                        });
                                      } else {
                                        setFormData({
                                          ...formData,
                                          products: currentProducts.filter((p) => p !== product),
                                        });
                                      }
                                    }}
                                    className="h-4 w-4 rounded border-slate-300 dark:border-slate-600"
                                  />
                                  <span className="text-sm text-slate-700 dark:text-slate-300">{product}</span>
                                </label>
                              );
                            })
                          ) : (
                            <p className="px-3 py-4 text-sm text-slate-500 dark:text-slate-400">
                              No products match &quot;{productSearchQuery}&quot;
                            </p>
                          );
                        })()}
                      </div>
                    </div>
                  )}
                </>
              )}
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {formData.products && formData.products.length > 0
                  ? `${formData.products.length} product${formData.products.length !== 1 ? "s" : ""} selected`
                  : "Select products to promote in the generated campaigns"}
              </p>
            </div>

            {generationError && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-300">
                {generationError}
              </div>
            )}

            {generationResult && (
              <div className="space-y-3 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4">
                <p className="text-sm font-semibold text-green-800 dark:text-green-200">
                  Campaign Generated Successfully!
                </p>
                <div className="mt-3 flex items-center justify-between gap-2 flex-wrap">
                  <div className="text-sm text-slate-600 dark:text-slate-300">
                    <strong>{generationResult.campaign_name}</strong>
                    <span className="ml-2 text-slate-500 dark:text-slate-400">({generationResult.campaign_id})</span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setEmailPreviewOpen(true)}
                    >
                      Preview Email
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(generationResult.html_email);
                        const btn = document.activeElement as HTMLButtonElement;
                        if (btn) {
                          const prev = btn.textContent;
                          btn.textContent = "Copied!";
                          setTimeout(() => { btn.textContent = prev; }, 1500);
                        }
                      }}
                    >
                      Copy HTML
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="outline" onClick={() => setGenerateDialogOpen(false)}>
            Close
          </Button>
          <Button onClick={handleGenerateCampaigns} disabled={generating}>
            {generating ? "Generating..." : "Generate Campaigns"}
          </Button>
        </DialogFooter>
      </Dialog>

      {/* Preview Email dialog: iframe with generated HTML */}
      <Dialog
        open={emailPreviewOpen && !!generationResult?.html_email}
        onOpenChange={(open) => {
          setEmailPreviewOpen(open);
        }}
        title="Preview Email"
        description={generationResult ? `${generationResult.campaign_name}` : undefined}
        contentClassName="max-w-5xl"
      >
        <DialogContent>
          <div className="rounded border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 overflow-hidden min-h-[480px]">
            <iframe
              title="Email preview"
              srcDoc={prepareCampaignHtmlForPreview(generationResult?.html_email ?? "")}
              className="w-full min-h-[480px] border-0 bg-white"
              sandbox="allow-same-origin"
              style={{ minHeight: "70vh" }}
            />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="outline" onClick={() => setEmailPreviewOpen(false)}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </Card>
  );
}
