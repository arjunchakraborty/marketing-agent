"use client";

import { useState, useCallback, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  uploadCampaignDataZip,
  uploadVectorDbZip,
  uploadProductsZip,
  type CampaignDataZipUploadResponse,
  type ProductZipUploadResponse,
} from "@/lib/api";

type UploadType = "campaign-data" | "products";

interface UploadResult {
  type: UploadType;
  success: boolean;
  message: string;
  data?: CampaignDataZipUploadResponse | ProductZipUploadResponse;
  error?: string;
}

export function DataUpload() {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState<UploadType>("campaign-data");
  const [campaignBusinessName, setCampaignBusinessName] = useState("");
  const [campaignCollectionName, setCampaignCollectionName] = useState("");
  const [replaceCollection, setReplaceCollection] = useState(false);
  const [productBusinessName, setProductBusinessName] = useState("");
  const [productCollectionName, setProductCollectionName] = useState("");

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
      let result: CampaignDataZipUploadResponse | ShopifyIntegrationZipUploadResponse | VectorDbZipUploadResponse | ProductZipUploadResponse;

      switch (activeTab) {
        case "campaign-data":
          result = await uploadVectorDbZip(selectedFile, {
            replaceCollection,
          });
          break;
        case "products":
          result = await uploadProductsZip(
            selectedFile,
            productBusinessName.trim() || undefined,
            productCollectionName || undefined
          );
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
                <p className="font-semibold">Image Analysis & Vector DB Loading:</p>
                {uploadResult.data.vector_db_loading.status === "error" ? (
                  <p className="text-red-600 dark:text-red-400">
                    Error: {uploadResult.data.vector_db_loading.error}
                  </p>
                ) : (
                  <>
                    <p>Loaded: {uploadResult.data.vector_db_loading.loaded} campaigns</p>
                    <p>With Images: {uploadResult.data.vector_db_loading.campaigns_with_images}</p>
                    <p>Without Images: {uploadResult.data.vector_db_loading.campaigns_without_images}</p>
                    <p>Collection: {uploadResult.data.vector_db_loading.collection_name}</p>
                    {uploadResult.data.vector_db_loading.skipped > 0 && (
                      <p>Skipped (already exists): {uploadResult.data.vector_db_loading.skipped}</p>
                    )}
                  </>
                )}
              </div>
            )}
            {uploadResult.type === "campaign-data" && !uploadResult.data.vector_db_loading && (
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 italic">
                  Note: No image-analysis-extract folder found. Only CSV data was ingested.
                </p>
              </div>
            )}
            {uploadResult.type === "products" && uploadResult.data.details && (
              <div>
                <p className="font-semibold">Product Ingestion:</p>
                <p>Products Processed: {uploadResult.data.details.products_processed}</p>
                <p>Images Stored: {uploadResult.data.details.images_stored}</p>
                <p>Collection: {uploadResult.data.details.collection_name}</p>
                {uploadResult.data.details.product_ids.length > 0 && (
                  <div className="mt-2">
                    <p className="font-semibold">Product IDs:</p>
                    <p className="text-xs break-words">
                      {uploadResult.data.details.product_ids.slice(0, 10).join(", ")}
                      {uploadResult.data.details.product_ids.length > 10 && "..."}
                    </p>
                  </div>
                )}
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
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="campaign-data">Campaign Data</TabsTrigger>
            <TabsTrigger value="products">Products</TabsTrigger>
          </TabsList>

          <TabsContent value="campaign-data" className="space-y-4">
            <div className="space-y-2">
              <Label>Expected Structure</Label>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                • email_campaigns.csv (or any CSV file)<br />
                • image-analysis-extract/ folder with JSON files
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="campaign-business">Business Name (Optional)</Label>
              <Input
                id="campaign-business"
                type="text"
                value={campaignBusinessName}
                onChange={(e) => setCampaignBusinessName(e.target.value)}
                placeholder="Auto-extracted from zip filename if not provided"
              />
              <p className="text-xs text-slate-600 dark:text-slate-400">
                If not provided, business name will be extracted from the zip filename.
                Example: "UCO_Gear_Campaigns.zip" → "UCO_Gear"
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="campaign-collection">Collection Name (Optional)</Label>
              <Input
                id="campaign-collection"
                type="text"
                value={campaignCollectionName}
                onChange={(e) => setCampaignCollectionName(e.target.value)}
                placeholder="Default: campaigns_{business_name} or campaign_data"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                id="replace-collection"
                type="checkbox"
                checked={replaceCollection}
                onChange={(e) => setReplaceCollection(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300"
              />
              <Label htmlFor="replace-collection" className="cursor-pointer font-normal">
                Replace collection (recreate with cosine for better search)
              </Label>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Check this to delete the existing campaign collection before loading so it is recreated with cosine distance. Use once to fix search ranking (e.g. for queries like &quot;Camp Chef Knife&quot;).
            </p>
          </TabsContent>

          <TabsContent value="products" className="space-y-4">
            <div className="space-y-2">
              <Label>Expected Structure</Label>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                • products.csv or products.json (product data)<br />
                • images/ folder with product images (*.jpg, *.png, etc.)<br />
                <br />
                Or flat structure:<br />
                • products.csv or products.json<br />
                • product_image_1.jpg, product_image_2.png, etc.
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="product-business">Business Name (Optional)</Label>
              <Input
                id="product-business"
                type="text"
                value={productBusinessName}
                onChange={(e) => setProductBusinessName(e.target.value)}
                placeholder="Auto-extracted from zip filename if not provided"
              />
              <p className="text-xs text-slate-600 dark:text-slate-400">
                If not provided, business name will be extracted from the zip filename.
                Example: "acme_products.zip" → "acme"
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="product-collection">Collection Name (Optional)</Label>
              <Input
                id="product-collection"
                type="text"
                value={productCollectionName}
                onChange={(e) => setProductCollectionName(e.target.value)}
                placeholder="Default: UCO_Gear_Products"
              />
            </div>
            <div className="space-y-2">
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Images will be stored in: storage/product_images/{`{business_name}`}/{`{product_id}`}/
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

