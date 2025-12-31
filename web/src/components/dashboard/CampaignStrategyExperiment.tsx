"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";

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
    setIsRunning(true);
    setError(null);
    setCurrentExperiment(null);
    setExperimentResults(null);

    try {
      const response = await fetch(`${API_BASE}/v1/experiments/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sql_query: sqlQuery || undefined,
          prompt_query: promptQuery || undefined,
          image_directory: imageDirectory || undefined,
          experiment_name: experimentName || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Experiment failed");
      }

      const result: ExperimentRun = await response.json();
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
      const response = await fetch(`${API_BASE}/v1/experiments/${experimentRunId}`);
      if (response.ok) {
        const results: ExperimentResults = await response.json();
        setExperimentResults(results);
      }
    } catch (err) {
      console.error("Failed to load experiment results:", err);
    }
  };

  const generateSqlFromPrompt = async () => {
    if (!promptQuery.trim()) return;

    try {
      const response = await fetch(`${API_BASE}/v1/analytics/prompt-sql`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: promptQuery }),
      });

      if (response.ok) {
        const data = await response.json();
        setSqlQuery(data.sql || "");
      }
    } catch (err) {
      console.error("Failed to generate SQL:", err);
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
              <Button onClick={generateSqlFromPrompt} variant="outline" size="sm">
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

          <Button onClick={runExperiment} disabled={isRunning} className="w-full">
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
                        {campaign.metrics && (
                          <div className="mt-2 text-xs text-slate-600 dark:text-slate-300">
                            Open Rate: {((campaign.metrics.open_rate || 0) * 100).toFixed(2)}% | 
                            Conversion: {((campaign.metrics.conversion_rate || 0) * 100).toFixed(2)}% |
                            Revenue: ${(campaign.metrics.revenue || 0).toFixed(2)}
                          </div>
                        )}
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
                            {image.dominant_colors.slice(0, 5).map((color, cidx) => (
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

