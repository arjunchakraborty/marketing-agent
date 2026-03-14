"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import {
  listCampaigns,
  getCampaign,
  prepareCampaignHtmlForPreview,
  type EmailCampaignListItem,
  type EmailCampaignResponse,
} from "@/lib/api";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<EmailCampaignListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewCampaign, setPreviewCampaign] = useState<EmailCampaignResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await listCampaigns(20, 0);
        if (!cancelled) {
          setCampaigns(res.campaigns);
          setTotal(res.total);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load campaigns");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  async function openPreview(campaignId: string) {
    setPreviewLoading(true);
    setPreviewCampaign(null);
    try {
      const campaign = await getCampaign(campaignId);
      setPreviewCampaign(campaign);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load campaign");
    } finally {
      setPreviewLoading(false);
    }
  }

  const formattedDate = (raw: string) => {
    try {
      const d = new Date(raw);
      return isNaN(d.getTime()) ? raw : d.toLocaleDateString(undefined, { dateStyle: "medium" });
    } catch {
      return raw;
    }
  };

  return (
    <div className="p-6 md:p-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Campaigns</h1>
          <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">
            Create and manage your email campaigns.
          </p>
        </div>
        <Button asChild>
          <Link href="/dashboard/recommendations">Create campaign</Link>
        </Button>
      </div>

      <Card className="mt-8">
        <CardHeader>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Your campaigns</h2>
        </CardHeader>
        <CardContent>
          {error && (
            <p className="text-sm text-red-600 dark:text-red-400 mb-4">{error}</p>
          )}
          {loading ? (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading campaigns…</p>
          ) : campaigns.length === 0 ? (
            <>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                No campaigns yet. Create your first one to get started.
              </p>
              <Button asChild variant="outline" className="mt-4">
                <Link href="/dashboard/recommendations">Create campaign</Link>
              </Button>
            </>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                {total} campaign{total !== 1 ? "s" : ""}
              </p>
              <ul className="divide-y divide-zinc-200 dark:divide-zinc-700">
                {campaigns.map((c) => (
                  <li
                    key={c.campaign_id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 py-3 first:pt-0"
                  >
                    <div>
                      <span className="font-medium text-zinc-900 dark:text-zinc-100">
                        {c.campaign_name || c.campaign_id}
                      </span>
                      <span className="ml-2 text-sm text-zinc-500 dark:text-zinc-400">
                        {formattedDate(c.generated_at)}
                      </span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openPreview(c.campaign_id)}
                    >
                      Preview
                    </Button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={!!previewCampaign || previewLoading}
        onOpenChange={(open) => {
          if (!open) {
            setPreviewCampaign(null);
            setPreviewLoading(false);
          }
        }}
        title={previewCampaign?.campaign_name ?? "Preview"}
        description={previewCampaign ? "Email content preview" : undefined}
        contentClassName="max-w-4xl w-full max-h-[90vh] flex flex-col"
      >
        <div className="flex-1 min-h-0 flex flex-col">
          {previewLoading ? (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading…</p>
          ) : previewCampaign ? (
            <iframe
              title="Campaign preview"
              srcDoc={prepareCampaignHtmlForPreview(previewCampaign.html_email)}
              className="w-full flex-1 min-h-[400px] border border-zinc-200 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900"
              sandbox="allow-same-origin"
            />
          ) : null}
        </div>
      </Dialog>
    </div>
  );
}
