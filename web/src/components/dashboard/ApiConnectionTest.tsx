"use client";

import { useState } from "react";

export function ApiConnectionTest() {
  const [status, setStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [message, setMessage] = useState<string>("");
  const [apiBase, setApiBase] = useState<string>("");

  const testConnection = async () => {
    setStatus("testing");
    setMessage("Testing connection...");
    
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:2121/api";
    setApiBase(base);
    
    try {
      console.log("[Test] Attempting to fetch from:", `${base}/v1/health`);
      const response = await fetch(`${base}/v1/health`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      console.log("[Test] Response status:", response.status);
      console.log("[Test] Response headers:", Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }
      
      const data = await response.json();
      setStatus("success");
      setMessage(`✅ Connection successful! Response: ${JSON.stringify(data)}`);
    } catch (error: any) {
      setStatus("error");
      const errorMsg = error.message || String(error);
      setMessage(`❌ Connection failed: ${errorMsg}`);
      console.error("[Test] Full error:", error);
    }
  };

  return (
    <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-2">
        API Connection Test
      </h3>
      <div className="space-y-2">
        <div className="text-xs text-slate-600 dark:text-slate-300">
          API Base: {apiBase || process.env.NEXT_PUBLIC_API_BASE || "http://localhost:2121/api"}
        </div>
        <button
          onClick={testConnection}
          disabled={status === "testing"}
          className="min-h-[44px] px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {status === "testing" ? "Testing..." : "Test Connection"}
        </button>
        {message && (
          <div
            className={`text-xs p-2 rounded ${
              status === "success"
                ? "bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200"
                : status === "error"
                ? "bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200"
                : "bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
            }`}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

