"use client";

import { useState, useCallback, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  uploadCampaignDataZip,
  uploadShopifyIntegrationZip,
  uploadVectorDbZip,
  type CampaignDataZipUploadResponse,
  type ShopifyIntegrationZipUploadResponse,
  type VectorDbZipUploadResponse,
} from "@/lib/api";

type UploadType = "campaign-data" | "shopify-integration" | "vector-db";

interface UploadResult {
  type: UploadType;
  success: boolean;
  message: string;
  data?: CampaignDataZipUploadResponse | ShopifyIntegrationZipUploadResponse | VectorDbZipUploadResponse;
  error?: string;
}

export function DataUpload() {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState<UploadType>("campaign-data");
  const [business, setBusiness] = useState("");

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith(".zip")) {
        setSelectedFile(file);
      } else {
        setUploadResult({
          type: activeTab,
          success: false,
          message: "Please upload a .zip file",
        });
      }
    }
  }, [activeTab]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.endsWith(".zip")) {
        setSelectedFile(file);
      } else {
        setUploadResult({
          type: activeTab,
          success: false,
          message: "Please upload a .zip file",
        });
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadResult({
        type: activeTab,
        success: false,
        message: "Please select a file to upload",
      });
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      let result: CampaignDataZipUploadResponse | ShopifyIntegrationZipUploadResponse | VectorDbZipUploadResponse;

      switch (activeTab) {
        case "campaign-data":
          result = await uploadCampaignDataZip(selectedFile);
          break;
        case "shopify-integration":
          result = await uploadShopifyIntegrationZip(selectedFile, business || undefined);
          break;
        case "vector-db":
          result = await uploadVectorDbZip(selectedFile);
          break;
        default:
          throw new Error("Invalid upload type");
      }

      setUploadResult({
        type: activeTab,
        success: true,
        message: "Upload successful!",
        data: result,
      });
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      setUploadResult({
        type: activeTab,
        success: false,
        message: "Upload failed",
        error: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  const renderResult = () => {
    if (!uploadResult) return null;

    if (!uploadResult.success) {
      return (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-sm font-medium text-red-800 dark:text-red-200">
            {uploadResult.message}
          </p>
          {uploadResult.error && (
            <p className="mt-2 text-xs text-red-600 dark:text-red-300">{uploadResult.error}</p>
          )}
        </div>
      );
    }

    return (
      <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
        <p className="text-sm font-medium text-green-800 dark:text-green-200">
          {uploadResult.message}
        </p>
        {uploadResult.data && (
          <div className="mt-3 space-y-2 text-xs text-green-700 dark:text-green-300">
            {uploadResult.type === "campaign-data" && uploadResult.data.csv_ingestion && (
              <div>
                <p className="font-semibold">CSV Ingestion:</p>
                <p>Table: {uploadResult.data.csv_ingestion.table_name}</p>
                <p>Total Rows: {uploadResult.data.csv_ingestion.total_rows}</p>
                <p>Inserted: {uploadResult.data.csv_ingestion.inserted}</p>
                <p>Updated: {uploadResult.data.csv_ingestion.updated}</p>
              </div>
            )}
            {uploadResult.type === "campaign-data" && uploadResult.data.vector_db_loading && (
              <div>
                <p className="font-semibold">Vector DB Loading:</p>
                <p>Loaded: {uploadResult.data.vector_db_loading.loaded} campaigns</p>
                <p>With Images: {uploadResult.data.vector_db_loading.campaigns_with_images}</p>
              </div>
            )}
            {uploadResult.type === "shopify-integration" && uploadResult.data.details && (
              <div>
                <p className="font-semibold">Shopify Integration:</p>
                <p>Datasets Ingested: {uploadResult.data.details.ingested_count}</p>
                {uploadResult.data.details.datasets.length > 0 && (
                  <div className="mt-2">
                    <p className="font-semibold">Tables Created:</p>
                    <ul className="list-disc list-inside">
                      {uploadResult.data.details.datasets.map((ds) => (
                        <li key={ds.table_name}>
                          {ds.table_name} ({ds.row_count} rows)
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {uploadResult.type === "vector-db" && uploadResult.data.details && (
              <div>
                <p className="font-semibold">Vector DB Loading:</p>
                <p>Loaded: {uploadResult.data.details.loaded} campaigns</p>
                <p>With Images: {uploadResult.data.details.campaigns_with_images}</p>
                <p>Collection: {uploadResult.data.details.collection_name}</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Upload</CardTitle>
        <CardDescription>
          Upload zip files to initialize databases. Files are automatically processed and cleaned up after upload.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as UploadType)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="campaign-data">Campaign Data</TabsTrigger>
            <TabsTrigger value="shopify-integration">Shopify Integration</TabsTrigger>
            <TabsTrigger value="vector-db">Vector DB</TabsTrigger>
          </TabsList>

          <TabsContent value="campaign-data" className="space-y-4">
            <div className="space-y-2">
              <Label>Expected Structure</Label>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                • email_campaigns.csv (or any CSV file)<br />
                • image-analysis-extract/ folder with JSON files
              </p>
            </div>
          </TabsContent>

          <TabsContent value="shopify-integration" className="space-y-4">
            <div className="space-y-2">
              <Label>Expected Structure</Label>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                • business_name/<br />
                &nbsp;&nbsp;• category/<br />
                &nbsp;&nbsp;&nbsp;&nbsp;• dataset.csv
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="business">Business Name (Optional)</Label>
              <input
                id="business"
                type="text"
                value={business}
                onChange={(e) => setBusiness(e.target.value)}
                placeholder="Filter by business name"
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800"
              />
            </div>
          </TabsContent>

          <TabsContent value="vector-db" className="space-y-4">
            <div className="space-y-2">
              <Label>Expected Structure</Label>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                • email_campaigns.csv (or any CSV file)<br />
                • image-analysis-extract/ folder with JSON files
              </p>
            </div>
          </TabsContent>
        </Tabs>

        <div
          className={`mt-6 rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
            dragActive
              ? "border-slate-400 bg-slate-100 dark:border-slate-500 dark:bg-slate-700"
              : "border-slate-300 bg-slate-50 dark:border-slate-600 dark:bg-slate-800/50"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          {selectedFile ? (
            <div className="space-y-2">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {formatFileSize(selectedFile.size)}
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedFile(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                  }
                }}
              >
                Remove
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Drag and drop a zip file here, or
              </p>
              <label htmlFor="file-upload">
                <Button variant="outline" size="sm" asChild>
                  <span>Browse Files</span>
                </Button>
              </label>
            </div>
          )}
        </div>

        <div className="mt-4 flex justify-end">
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            size="lg"
          >
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </div>

        {renderResult()}
      </CardContent>
    </Card>
  );
}

