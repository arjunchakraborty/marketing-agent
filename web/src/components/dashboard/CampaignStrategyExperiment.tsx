"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { generateSqlFromPrompt } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:2121/api";

interface ExperimentRun {
  experiment_run_id: string;
  status: string;
  campaigns_analyzed: number;
  images_analyzed: number;
  visual_elements_found: number;
  campaign_ids: string[];
  products_promoted: string[];
}

interface ExperimentResults {
  experiment_run: {
    experiment_run_id: string;
    name: string;
    description: string;
    sql_query: string;
    status: string;
    results_summary: any;
    created_at: string;
  };
  campaign_analyses: any[];
  image_analyses: any[];
  correlations: any[];
}

export function CampaignStrategyExperiment() {
  const [sqlQuery, setSqlQuery] = useState(`SELECT campaign_id, campaign_name, open_rate, click_rate, conversion_rate, revenue
FROM campaigns
WHERE open_rate > 0.3 OR conversion_rate > 0.01
ORDER BY conversion_rate DESC, revenue DESC
LIMIT 20`);
  const [promptQuery, setPromptQuery] = useState("");
  const [imageDirectory, setImageDirectory] = useState("/Users/kerrief/projects/klyaviyo");
  const [experimentName, setExperimentName] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [currentExperiment, setCurrentExperiment] = useState<ExperimentRun | null>(null);
  const [experimentResults, setExperimentResults] = useState<ExperimentResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runExperiment = async () => {
    console.log("[CampaignStrategy] Starting experiment...");
    setIsRunning(true);
    setError(null);
    setCurrentExperiment(null);
    setExperimentResults(null);

    try {
      // Validate inputs
      if (!sqlQuery.trim() && !promptQuery.trim()) {
        throw new Error("Please provide either a SQL query or a natural language prompt");
      }

      // If prompt query is provided but no SQL, generate SQL first
      let finalSqlQuery = sqlQuery;
      if (promptQuery.trim() && !sqlQuery.trim()) {
        console.log("[CampaignStrategy] Generating SQL from prompt...");
        try {
          const sqlData = await generateSqlFromPrompt(promptQuery);
          finalSqlQuery = sqlData.sql || "";
          setSqlQuery(finalSqlQuery);
          console.log("[CampaignStrategy] SQL generated:", finalSqlQuery.substring(0, 100));
        } catch (err: any) {
          throw new Error(`Failed to generate SQL from prompt: ${err.message}`);
        }
      }

      if (!finalSqlQuery.trim()) {
        throw new Error("SQL query is required to run the experiment");
      }

      const requestBody = {
        sql_query: finalSqlQuery || undefined,
        prompt_query: promptQuery || undefined,
        image_directory: imageDirectory || undefined,
        experiment_name: experimentName || undefined,
      };

      console.log("[CampaignStrategy] Sending request to:", `${API_BASE}/v1/experiments/run`);
      console.log("[CampaignStrategy] Request body:", requestBody);

      // Add timeout to fetch request (60 seconds)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      const response = await fetch(`${API_BASE}/v1/experiments/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      console.log("[CampaignStrategy] Response status:", response.status, response.statusText);

      if (!response.ok) {
        let errorMessage = "Experiment failed";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const result: ExperimentRun = await response.json();
      console.log("[CampaignStrategy] Experiment result:", result);
      setCurrentExperiment(result);

      // Fetch full results
      if (result.experiment_run_id) {
        console.log("[CampaignStrategy] Loading full results for:", result.experiment_run_id);
        await loadExperimentResults(result.experiment_run_id);
      }
    } catch (err: any) {
      console.error("[CampaignStrategy] Experiment error:", err);
      if (err.name === "AbortError") {
        setError("Request timed out. The experiment may be taking longer than expected.");
      } else {
        setError(err.message || "Failed to run experiment");
      }
    } finally {
      setIsRunning(false);
      console.log("[CampaignStrategy] Experiment finished");
    }
  };

  const loadExperimentResults = async (experimentRunId: string) => {
    try {
      console.log("[CampaignStrategy] Loading results for:", experimentRunId);
      const response = await fetch(`${API_BASE}/v1/experiments/${experimentRunId}`);
      console.log("[CampaignStrategy] Results response status:", response.status);
      
      if (response.ok) {
        const results: ExperimentResults = await response.json();
        console.log("[CampaignStrategy] Results loaded:", {
          campaigns: results.campaign_analyses?.length || 0,
          images: results.image_analyses?.length || 0,
          correlations: results.correlations?.length || 0,
          fullResults: results
        });
        setExperimentResults(results);
      } else {
        const errorText = await response.text();
        console.warn(`[CampaignStrategy] Failed to load experiment results: ${response.status}`, errorText);
        setError(`Failed to load detailed results: ${response.status}`);
      }
    } catch (err) {
      console.error("[CampaignStrategy] Failed to load experiment results:", err);
      setError(`Failed to load results: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleGenerateSqlFromPrompt = async () => {
    if (!promptQuery.trim()) {
      setError("Please enter a prompt query");
      return;
    }

    try {
      const data = await generateSqlFromPrompt(promptQuery);
      setSqlQuery(data.sql || "");
      setError(null);
    } catch (err: any) {
      console.error("Failed to generate SQL:", err);
      setError(err.message || "Failed to generate SQL from prompt");
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Campaign Strategy Analysis Agent</CardTitle>
          <CardDescription>
            Analyze Klaviyo campaigns and images to identify the most impactful visual elements
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="experiment-name">Experiment Name (Optional)</Label>
            <Input
              id="experiment-name"
              value={experimentName}
              onChange={(e) => setExperimentName(e.target.value)}
              placeholder="e.g., Black Friday Campaign Analysis"
            />
          </div>

          <Tabs defaultValue="sql" className="w-full">
            <TabsList>
              <TabsTrigger value="sql">SQL Query</TabsTrigger>
              <TabsTrigger value="prompt">Natural Language Prompt</TabsTrigger>
            </TabsList>
            <TabsContent value="sql" className="space-y-2">
              <Label htmlFor="sql-query">SQL Query to Find Impactful Campaigns</Label>
              <Textarea
                id="sql-query"
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                placeholder="SELECT campaign_id, campaign_name, open_rate, conversion_rate FROM campaigns WHERE conversion_rate > 0.05 ORDER BY conversion_rate DESC LIMIT 20"
                rows={8}
                className="font-mono text-sm"
              />
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Write SQL to query campaigns. The query should return campaign_id, campaign_name, and performance metrics.
                You can adjust this SQL to refine your analysis.
              </p>
            </TabsContent>
            <TabsContent value="prompt" className="space-y-2">
              <Label htmlFor="prompt-query">Natural Language Query</Label>
              <Textarea
                id="prompt-query"
                value={promptQuery}
                onChange={(e) => setPromptQuery(e.target.value)}
                placeholder="Find the top 20 campaigns with the highest conversion rates from the last 3 months"
                rows={4}
              />
              <Button onClick={handleGenerateSqlFromPrompt} variant="outline" size="sm">
                Generate SQL from Prompt
              </Button>
            </TabsContent>
          </Tabs>

          <div className="space-y-2">
            <Label htmlFor="image-directory">Image Directory Path</Label>
            <Input
              id="image-directory"
              value={imageDirectory}
              onChange={(e) => setImageDirectory(e.target.value)}
              placeholder="/path/to/campaign/images"
            />
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Path to directory containing campaign images. Campaign IDs should be in filenames (e.g., campaign_01K4QVNYM1QKSK61X7PXR019DF.png).
            </p>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-300">
              {error}
            </div>
          )}

          <Button 
            onClick={() => {
              console.log("[CampaignStrategy] Button clicked");
              runExperiment();
            }} 
            disabled={isRunning} 
            className="w-full"
          >
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
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-slate-500 dark:text-slate-400">Campaigns Analyzed</div>
                <div className="text-2xl font-bold dark:text-slate-100">{currentExperiment.campaigns_analyzed}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 dark:text-slate-400">Images Analyzed</div>
                <div className="text-2xl font-bold dark:text-slate-100">{currentExperiment.images_analyzed}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 dark:text-slate-400">Visual Elements Found</div>
                <div className="text-2xl font-bold dark:text-slate-100">{currentExperiment.visual_elements_found}</div>
              </div>
            </div>

            {currentExperiment.products_promoted.length > 0 && (
              <div>
                <div className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Top Products Promoted</div>
                <div className="flex flex-wrap gap-2">
                  {currentExperiment.products_promoted.slice(0, 10).map((product, idx) => (
                    <span key={idx} className="rounded-full bg-blue-100 px-3 py-1 text-xs text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                      {product}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {experimentResults ? (
              <Tabs defaultValue="campaigns" className="w-full">
                <TabsList>
                  <TabsTrigger value="campaigns">
                    Campaigns ({experimentResults.campaign_analyses?.length || 0})
                  </TabsTrigger>
                  <TabsTrigger value="images">
                    Image Analysis ({experimentResults.image_analyses?.length || 0})
                  </TabsTrigger>
                  <TabsTrigger value="correlations">
                    Visual Correlations ({experimentResults.correlations?.length || 0})
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="campaigns">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {experimentResults.campaign_analyses && experimentResults.campaign_analyses.length > 0 ? (
                      experimentResults.campaign_analyses.map((campaign, idx) => (
                        <div key={idx} className="rounded border border-slate-200 dark:border-slate-700 p-3 text-sm dark:bg-slate-800">
                          <div className="font-semibold dark:text-slate-100">
                            {campaign.campaign_name || campaign.campaign_id || `Campaign ${idx + 1}`}
                          </div>
                          {campaign.metrics && (
                            <div className="mt-2 text-xs text-slate-600 dark:text-slate-300">
                              Open Rate: {((campaign.metrics.open_rate || 0) * 100).toFixed(2)}% | 
                              Conversion: {((campaign.metrics.conversion_rate || 0) * 100).toFixed(2)}% |
                              Revenue: ${(campaign.metrics.revenue || 0).toFixed(2)}
                            </div>
                          )}
                          {campaign.query_results && (
                            <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                              Query returned {Array.isArray(campaign.query_results) ? campaign.query_results.length : 'N/A'} results
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-slate-500 dark:text-slate-400 p-4 text-center">
                        No campaign analyses available yet.
                      </div>
                    )}
                  </div>
                </TabsContent>
                <TabsContent value="images">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {experimentResults.image_analyses && experimentResults.image_analyses.length > 0 ? (
                      experimentResults.image_analyses.map((image, idx) => (
                        <div key={idx} className="rounded border border-slate-200 dark:border-slate-700 p-3 text-sm dark:bg-slate-800">
                          <div className="font-semibold dark:text-slate-100">
                            Campaign: {image.campaign_id || "Unknown"} | Image: {image.image_id}
                          </div>
                          {image.overall_description && (
                            <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                              {image.overall_description}
                            </div>
                          )}
                          {image.dominant_colors && image.dominant_colors.length > 0 && (
                            <div className="mt-2 flex gap-1 flex-wrap">
                              {image.dominant_colors.slice(0, 5).map((color, cidx) => (
                                <span key={cidx} className="rounded px-2 py-1 text-xs bg-slate-100 dark:bg-slate-700 dark:text-slate-300">
                                  {typeof color === 'string' ? color : JSON.stringify(color)}
                                </span>
                              ))}
                            </div>
                          )}
                          {image.composition_analysis && (
                            <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                              Composition: {image.composition_analysis}
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-slate-500 dark:text-slate-400 p-4 text-center">
                        No image analyses available. {imageDirectory ? 'Check if images exist in the specified directory.' : 'No image directory specified.'}
                      </div>
                    )}
                  </div>
                </TabsContent>
                <TabsContent value="correlations">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {experimentResults.correlations && experimentResults.correlations.length > 0 ? (
                      experimentResults.correlations.map((corr, idx) => (
                        <div key={idx} className="rounded border border-slate-200 dark:border-slate-700 p-3 text-sm dark:bg-slate-800">
                          <div className="font-semibold dark:text-slate-100">{corr.element_type || 'Unknown Element'}</div>
                          {corr.element_description && (
                            <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{corr.element_description}</div>
                          )}
                          <div className="mt-2 text-xs dark:text-slate-300">
                            {corr.performance_impact && (
                              <>
                                <div className="font-semibold">Impact:</div>
                                <div>{corr.performance_impact}</div>
                              </>
                            )}
                            {corr.recommendation && (
                              <>
                                <div className="font-semibold mt-2">Recommendation:</div>
                                <div>{corr.recommendation}</div>
                              </>
                            )}
                            {corr.campaign_count !== undefined && (
                              <div className="mt-2 text-slate-500">
                                Found in {corr.campaign_count} campaign(s)
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-slate-500 dark:text-slate-400 p-4 text-center">
                        No visual correlations found yet. Correlations are generated when both campaign data and image analyses are available.
                      </div>
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            ) : (
              <div className="text-sm text-slate-500 dark:text-slate-400 p-4 text-center">
                Loading detailed results...
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

