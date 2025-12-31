"use client";

import { useEffect, useState } from "react";
import { listExperiments, generateEmailCampaign, type ExperimentResultsResponse, type EmailCampaignGenerationRequest, type EmailCampaignResponse } from "@/lib/api";
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
  const [availableProducts, setAvailableProducts] = useState<string[]>([]);
  
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
    
    const exp = experiments.find(e => e.experiment_run.experiment_run_id === experimentId);
    const products: string[] = [];
    
    if (exp) {
      exp.campaign_analyses.forEach((campaign) => {
        if (campaign.products_promoted && Array.isArray(campaign.products_promoted)) {
          campaign.products_promoted.forEach((product: string) => {
            if (product && !products.includes(product)) {
              products.push(product);
            }
          });
        }
      });
      
      const resultsSummary = exp.experiment_run.results_summary || {};
      if (resultsSummary.products_promoted && Array.isArray(resultsSummary.products_promoted)) {
        resultsSummary.products_promoted.forEach((product: string) => {
          if (product && !products.includes(product)) {
            products.push(product);
          }
        });
      }
    }
    
    setAvailableProducts(products);
    
    let initialStrategyFocus = "";
    if (summary.recommendations && summary.recommendations.length > 0) {
      initialStrategyFocus = summary.recommendations.join("\n• ");
      initialStrategyFocus = "Recommendations:\n• " + initialStrategyFocus;
    } else if (summary.summary) {
      initialStrategyFocus = summary.summary;
    }
    
    if (summary.key_features && summary.key_features.length > 0) {
      const featuresText = "\n\nKey Features:\n• " + summary.key_features.join("\n• ");
      initialStrategyFocus += featuresText;
    }
    
    if (summary.patterns) {
      const patternsText = "\n\nPatterns:\n";
      let patternsList: string[] = [];
      if (summary.patterns.visual) patternsList.push(`Visual: ${summary.patterns.visual}`);
      if (summary.patterns.messaging) patternsList.push(`Messaging: ${summary.patterns.messaging}`);
      if (summary.patterns.design) patternsList.push(`Design: ${summary.patterns.design}`);
      if (patternsList.length > 0) {
        initialStrategyFocus += patternsText + patternsList.join("\n");
      }
    }
    
    setFormData({
      objective: initialStrategyFocus || "Generate email campaign based on experiment insights",
      products: products.length > 0 ? products.slice(0, 5) : [],
      key_message: initialStrategyFocus,
      design_guidance: initialStrategyFocus,
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
    if (!formData.objective || !formData.objective.trim()) {
      setGenerationError("Campaign objective is required");
      return;
    }

    if (!formData.products || formData.products.length === 0) {
      setGenerationError("Please select at least one product");
      return;
    }

    setGenerating(true);
    setGenerationError(null);
    setGenerationResult(null);

    try {
      const result = await generateEmailCampaign(formData);
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
                        {summary.recommendations && summary.recommendations.length > 0 && (
                          <>
                            <span>•</span>
                            <span>{summary.recommendations.length} recommendations</span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Button variant="ghost" size="sm" onClick={() => setExpandedExperiment(isExpanded ? null : summary.experiment_run_id)}>
                        {isExpanded ? "Hide" : "Show Details"}
                      </Button>
                      {summary.recommendations && summary.recommendations.length > 0 && (
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
                          Recommendations ({summary.recommendations?.length || 0})
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
                        {summary.recommendations && summary.recommendations.length > 0 ? (
                          <ul className="list-disc list-inside space-y-2 text-sm text-slate-600 dark:text-slate-300">
                            {summary.recommendations.map((rec, idx) => (
                              <li key={idx}>{rec}</li>
                            ))}
                          </ul>
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
        onOpenChange={setGenerateDialogOpen}
        title="Generate Campaigns"
        description="Configure campaign generation based on the selected recommendation"
      >
        <DialogContent>
          <div className="space-y-4">
            {selectedExperimentId && (() => {
              const exp = experiments.find(e => e.experiment_run.experiment_run_id === selectedExperimentId);
              if (!exp) return null;
              const summary = extractExperimentSummary(exp);
              return (
                <div className="space-y-2 rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3">
                  <div>
                    <p className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-1">Experiment ID:</p>
                    <p className="text-sm text-blue-700 dark:text-blue-300 font-mono">{selectedExperimentId}</p>
                  </div>
                  {summary.recommendations && summary.recommendations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
                      <p className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
                        Using all {summary.recommendations.length} recommendation{summary.recommendations.length !== 1 ? 's' : ''}:
                      </p>
                      <ul className="list-disc list-inside space-y-1 text-xs text-blue-700 dark:text-blue-300">
                        {summary.recommendations.map((rec, idx) => (
                          <li key={idx}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })()}

            <div className="space-y-2">
              <Label htmlFor="campaign-objective">Campaign Objective *</Label>
              <Textarea
                id="campaign-objective"
                value={formData.objective || ""}
                onChange={(e) => setFormData({ ...formData, objective: e.target.value })}
                placeholder="e.g., Increase sales, Promote new product, Re-engage customers"
                rows={3}
                required
              />
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Describe the main goal of this campaign
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="key-message">Key Message / Design Guidance</Label>
              <Textarea
                id="key-message"
                value={formData.key_message || ""}
                onChange={(e) => setFormData({ ...formData, key_message: e.target.value, design_guidance: e.target.value })}
                placeholder="Key message, value proposition, or design preferences"
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>Select Products</Label>
              {availableProducts.length > 0 ? (
                <div className="max-h-48 overflow-y-auto rounded border border-slate-200 dark:border-slate-700 p-3 space-y-2">
                  {availableProducts.map((product) => {
                    const isSelected = formData.products?.includes(product) || false;
                    return (
                      <label
                        key={product}
                        className="flex items-center gap-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 p-2 rounded"
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
                          className="rounded border-slate-300 dark:border-slate-600"
                        />
                        <span className="text-sm text-slate-700 dark:text-slate-300">{product}</span>
                      </label>
                    );
                  })}
                </div>
              ) : (
                <div className="rounded border border-slate-200 dark:border-slate-700 p-3">
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    No products found in this experiment. You can manually enter products below.
                  </p>
                </div>
              )}
              <div className="mt-2">
                <Label htmlFor="manual-products" className="text-xs text-slate-500 dark:text-slate-400">
                  Or enter products manually (comma-separated):
                </Label>
                <Input
                  id="manual-products"
                  type="text"
                  placeholder="Product 1, Product 2, Product 3"
                  onChange={(e) => {
                    const products = e.target.value
                      .split(",")
                      .map((p) => p.trim())
                      .filter((p) => p.length > 0);
                    setFormData({
                      ...formData,
                      products: products,
                    });
                  }}
                  className="mt-1"
                />
              </div>
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
                <div className="mt-3 space-y-3">
                  <div className="rounded border border-green-200 dark:border-green-800 bg-white dark:bg-slate-800 p-4">
                    <div className="font-semibold text-base text-slate-800 dark:text-slate-100 mb-2">
                      {generationResult.campaign_name}
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-300 mb-3">
                      <div><strong>Campaign ID:</strong> {generationResult.campaign_id}</div>
                      <div><strong>Objective:</strong> {generationResult.objective}</div>
                      {generationResult.audience_segment && (
                        <div><strong>Audience:</strong> {generationResult.audience_segment}</div>
                      )}
                    </div>
                    
                    <div className="border-t border-slate-200 dark:border-slate-700 pt-3 mt-3">
                      <div className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Email Content:</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                        <div><strong>Subject:</strong> {generationResult.email_content.subject_line}</div>
                        {generationResult.email_content.preview_text && (
                          <div><strong>Preview:</strong> {generationResult.email_content.preview_text}</div>
                        )}
                        <div className="mt-2 p-2 bg-slate-50 dark:bg-slate-900 rounded text-xs">
                          {generationResult.email_content.body}
                        </div>
                        <div className="mt-2"><strong>CTA:</strong> {generationResult.email_content.call_to_action}</div>
                      </div>
                    </div>

                    {generationResult.subject_line_variations && generationResult.subject_line_variations.length > 0 && (
                      <div className="border-t border-slate-200 dark:border-slate-700 pt-3 mt-3">
                        <div className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Subject Line Variations:</div>
                        <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-400 space-y-1">
                          {generationResult.subject_line_variations.map((line: string, idx: number) => (
                            <li key={idx}>{line}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {generationResult.design_recommendations && generationResult.design_recommendations.length > 0 && (
                      <div className="border-t border-slate-200 dark:border-slate-700 pt-3 mt-3">
                        <div className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Design Recommendations:</div>
                        <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-400 space-y-1">
                          {generationResult.design_recommendations.map((rec: string, idx: number) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {generationResult.expected_metrics && (
                      <div className="border-t border-slate-200 dark:border-slate-700 pt-3 mt-3">
                        <div className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Expected Metrics:</div>
                        <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                          {generationResult.expected_metrics.estimated_open_rate && (
                            <div>Open Rate: {generationResult.expected_metrics.estimated_open_rate}</div>
                          )}
                          {generationResult.expected_metrics.estimated_click_rate && (
                            <div>Click Rate: {generationResult.expected_metrics.estimated_click_rate}</div>
                          )}
                          {generationResult.expected_metrics.estimated_conversion_rate && (
                            <div>Conversion Rate: {generationResult.expected_metrics.estimated_conversion_rate}</div>
                          )}
                        </div>
                      </div>
                    )}
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
    </Card>
  );
}
