'use client';
import { useCallback, useEffect, useMemo, useState } from "react";

import { generateSqlFromPrompt } from "@/lib/api";

interface QueryResult {
  table_name: string;
  business: string;
  dataset_name: string;
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
}

const defaultPrompt =
  "Show me the top 5 product categories by total sales in the last month.";

export function PromptSqlExplorer() {
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);

  const runQuery = useCallback(
    async (promptValue: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const payload = await generateSqlFromPrompt(promptValue);
        setResult(payload);
      } catch (err) {
        console.error('[PromptSQL] Error:', err);
        let errorMessage = "Failed to generate SQL.";
        if (err instanceof Error) {
          errorMessage = err.message;
          // Provide more helpful error messages
          if (errorMessage.includes("Failed to fetch") || errorMessage.includes("NetworkError")) {
            errorMessage = "Unable to connect to the API. Please check if the backend server is running on port 2121.";
          } else if (errorMessage.includes("API key not configured") || errorMessage.includes("OpenAI API key")) {
            errorMessage = "LLM features require API configuration. The system will use heuristic mode instead. To enable LLM features, add your API key to backend/.env (see README for details).";
          } else if (errorMessage.includes("500") || errorMessage.includes("Internal Server")) {
            errorMessage = "Server error occurred. Please check the backend logs for details.";
          } else if (errorMessage.includes("No datasets")) {
            errorMessage = "No data has been ingested yet. Please upload sales data first.";
          }
        }
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [setResult],
  );

  // Disable auto-run on mount to prevent errors if LLM is not configured
  // useEffect(() => {
  //   runQuery(defaultPrompt);
  // }, [runQuery]);

  const previewColumns = useMemo(() => {
    if (!result?.rows?.length) return result?.columns ?? [];
    const row = result.rows[0];
    return Object.keys(row);
  }, [result]);

  return (
    <div className="flex h-full flex-col gap-6">
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Prompt-to-SQL Explorer</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Translate natural language questions into runnable SQL across your unified Shopify and CSV schemas.
          </p>
        </div>

        <label className="flex flex-col gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Prompt</span>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            className="min-h-[120px] w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 focus:border-slate-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-slate-500"
            placeholder="Ask a question about your marketing data..."
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => runQuery(prompt)}
            className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200 dark:disabled:bg-slate-600"
            disabled={isLoading || !prompt.trim()}
          >
            {isLoading ? "Generating..." : "Run Prompt"}
          </button>
          {result ? (
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
              matched dataset: <span className="text-slate-700 dark:text-slate-300">{result.dataset_name}</span>
            </p>
          ) : null}
          {error ? <p className="text-xs font-medium text-rose-600 dark:text-rose-400">{error}</p> : null}
        </div>
      </div>

      {result ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 transition-colors">
          <div className="flex flex-col gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              {result.business} / {result.dataset_name}
            </p>
            <pre className="overflow-auto rounded-lg bg-black p-4 font-mono text-xs text-lime-400 dark:bg-slate-900">
              {result.sql}
            </pre>
          </div>
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Preview</h3>
            <div className="mt-2 overflow-auto rounded-lg border border-slate-200 dark:border-slate-700">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs text-slate-600 dark:divide-slate-700 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-700">
                  <tr>
                    {previewColumns.map((column) => (
                      <th key={column} className="px-4 py-2 font-semibold text-slate-600 dark:text-slate-300">
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white dark:divide-slate-700 dark:bg-slate-800">
                  {result.rows.slice(0, 20).map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {previewColumns.map((column) => {
                        const value = row[column as keyof typeof row];
                        return (
                          <td key={column} className="px-4 py-2 text-slate-500 dark:text-slate-400">
                            {value == null ? "" : String(value)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

