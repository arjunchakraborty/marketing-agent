"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { runExperiment, getExperimentResults, type ExperimentRunResponse, type ExperimentResultsResponse } from "@/lib/api";

export function CampaignStrategyExperiment() {
  const [promptQuery, setPromptQuery] = useState("high performing email campaigns with high conversion rates");
  const [collectionName, setCollectionName] = useState("");
  const [experimentName, setExperimentName] = useState("");
  const [numCampaigns, setNumCampaigns] = useState(10);
  const [isRunning, setIsRunning] = useState(false);
  const [currentExperiment, setCurrentExperiment] = useState<ExperimentRunResponse | null>(null);
  const [experimentResults, setExperimentResults] = useState<ExperimentResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunExperiment = async () => {
    if (!promptQuery.trim()) {
      setError("Please provide a prompt query describing what campaigns to find");
      return;
    }

    setIsRunning(true);
    setError(null);
    setCurrentExperiment(null);
    setExperimentResults(null);

    try {
      const result = await runExperiment({
        prompt_query: promptQuery,
        collection_name: collectionName || undefined,
        experiment_name: experimentName || undefined,
        num_campaigns: numCampaigns,
      });

      setCurrentExperiment(result);

      // Fetch full results
      if (result.experiment_run_id) {
        await loadExperimentResults(result.experiment_run_id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to run experiment");
    } finally {
      setIsRunning(false);
    }
  };

  const loadExperimentResults = async (experimentRunId: string) => {
    try {
      const results = await getExperimentResults(experimentRunId);
      setExperimentResults(results);
    } catch (err) {
      console.error("Failed to load experiment results:", err);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Campaign Strategy Analysis Agent</CardTitle>
          <CardDescription>
            Use natural language to find campaigns in the vector database and extract key features, patterns, and recommendations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="prompt-query">Prompt Query *</Label>
            <Textarea
              id="prompt-query"
              value={promptQuery}
              onChange={(e) => setPromptQuery(e.target.value)}
              placeholder="e.g., high performing email campaigns with high conversion rates"
              rows={4}
              required
            />
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Describe what type of campaigns you want to analyze. Examples: "high performing email campaigns", 
              "campaigns with high conversion rates", "product launch campaigns", etc.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="experiment-name">Experiment Name (Optional)</Label>
              <Input
                id="experiment-name"
                value={experimentName}
                onChange={(e) => setExperimentName(e.target.value)}
                placeholder="e.g., Q1 Campaign Analysis"
              />
            </div>
          </div>



          {error && (
            <div className="rounded-md bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-300">
              {error}
            </div>
          )}

          <Button onClick={handleRunExperiment} disabled={isRunning || !promptQuery.trim()} className="w-full">
            {isRunning ? "Running Analysis..." : "Run Campaign Strategy Analysis"}
          </Button>
        </CardContent>
      </Card>

      {currentExperiment && (
        <Card>
          <CardHeader>
            <CardTitle>Experiment Results</CardTitle>
            <CardDescription>Experiment ID: {currentExperiment.experiment_run_id}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">

            {currentExperiment.key_features && (
              <div className="space-y-4">
                <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
                  <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-3">Key Features & Recommendations</h3>
                  
                  {currentExperiment.key_features.summary && (
                    <div className="mb-4 p-3 rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                      <p className="text-sm text-blue-800 dark:text-blue-200">{currentExperiment.key_features.summary}</p>
                    </div>
                  )}

                  {currentExperiment.key_features.key_features && currentExperiment.key_features.key_features.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Key Features</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm text-slate-600 dark:text-slate-300">
                        {currentExperiment.key_features.key_features.map((feature, idx) => (
                          <li key={idx}>{feature}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {currentExperiment.key_features.patterns && Object.keys(currentExperiment.key_features.patterns).length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Common Patterns</h4>
                      <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
                        {currentExperiment.key_features.patterns.visual && (
                          <div>
                            <span className="font-semibold">Visual: </span>
                            <span>{currentExperiment.key_features.patterns.visual}</span>
                          </div>
                        )}
                        {currentExperiment.key_features.patterns.messaging && (
                          <div>
                            <span className="font-semibold">Messaging: </span>
                            <span>{currentExperiment.key_features.patterns.messaging}</span>
                          </div>
                        )}
                        {currentExperiment.key_features.patterns.design && (
                          <div>
                            <span className="font-semibold">Design: </span>
                            <span>{currentExperiment.key_features.patterns.design}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {currentExperiment.key_features.recommendations && currentExperiment.key_features.recommendations.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Recommendations</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm text-slate-600 dark:text-slate-300">
                        {currentExperiment.key_features.recommendations.map((rec, idx) => (
                          <li key={idx}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {experimentResults && (
              <Tabs defaultValue="campaigns" className="w-full">
                <TabsList>
                  <TabsTrigger value="campaigns">Campaigns ({experimentResults.campaign_analyses.length})</TabsTrigger>
                  <TabsTrigger value="images">Image Analysis ({experimentResults.image_analyses.length})</TabsTrigger>
                  <TabsTrigger value="correlations">Visual Correlations ({experimentResults.correlations.length})</TabsTrigger>
                </TabsList>
                <TabsContent value="campaigns">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {experimentResults.campaign_analyses.map((campaign, idx) => (
                      <div key={idx} className="rounded border border-slate-200 dark:border-slate-700 p-3 text-sm dark:bg-slate-800">
                        <div className="font-semibold dark:text-slate-100">{campaign.campaign_name || campaign.campaign_id}</div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
                <TabsContent value="images">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {experimentResults.image_analyses.map((image, idx) => (
                      <div key={idx} className="rounded border border-slate-200 dark:border-slate-700 p-3 text-sm dark:bg-slate-800">
                        <div className="font-semibold dark:text-slate-100">Campaign: {image.campaign_id || "Unknown"}</div>
                        <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{image.overall_description}</div>
                        {image.dominant_colors && image.dominant_colors.length > 0 && (
                          <div className="mt-2 flex gap-1 flex-wrap">
                            {image.dominant_colors.slice(0, 5).map((color: string, cidx: number) => (
                              <span key={cidx} className="rounded px-2 py-1 text-xs bg-slate-100 dark:bg-slate-700 dark:text-slate-300">
                                {color}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </TabsContent>
                <TabsContent value="correlations">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {experimentResults.correlations.map((corr, idx) => (
                      <div key={idx} className="rounded border border-slate-200 dark:border-slate-700 p-3 text-sm dark:bg-slate-800">
                        <div className="font-semibold dark:text-slate-100">{corr.element_type}</div>
                        <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{corr.element_description}</div>
                        <div className="mt-2 text-xs dark:text-slate-300">
                          <div className="font-semibold">Impact:</div>
                          <div>{corr.performance_impact}</div>
                          <div className="font-semibold mt-2">Recommendation:</div>
                          <div>{corr.recommendation}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

