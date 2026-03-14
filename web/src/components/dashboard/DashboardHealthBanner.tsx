"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";

export function DashboardHealthBanner() {
  const [unreachable, setUnreachable] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then(() => {
        if (!cancelled) setUnreachable(false);
      })
      .catch(() => {
        if (!cancelled) setUnreachable(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (unreachable !== true) return null;

  return (
    <div
      className="bg-amber-100 px-4 py-2.5 text-center text-sm text-amber-900 dark:bg-amber-900/30 dark:text-amber-200"
      role="alert"
    >
      Can’t reach the server. Check that the backend is running and that{" "}
      <code className="rounded bg-amber-200/60 px-1.5 py-0.5 dark:bg-amber-800/40">
        NEXT_PUBLIC_API_BASE
      </code>{" "}
      points to it (e.g. <code className="rounded bg-amber-200/60 px-1.5 py-0.5 dark:bg-amber-800/40">http://localhost:8000/api</code> when running locally).
    </div>
  );
}
