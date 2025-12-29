"use client";

import { useState, useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:2121/api";

interface ImageUploaderProps {
  onUploadComplete?: (result: any) => void;
}

export function ImageUploader({ onUploadComplete }: ImageUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [campaignId, setCampaignId] = useState("");
  const [campaignName, setCampaignName] = useState("");

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files).filter((file) =>
        file.type.startsWith("image/")
      );
      if (files.length > 0) {
        await handleImageUpload(files[0]);
      }
    },
    [campaignId, campaignName]
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        await handleImageUpload(files[0]);
      }
    },
    [campaignId, campaignName]
  );

  const handleImageUpload = async (file: File) => {
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (campaignId) formData.append("campaign_id", campaignId);
      if (campaignName) formData.append("campaign_name", campaignName);

      const response = await fetch(`${API_BASE}/v1/image-analysis/analyze/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const result = await response.json();
      setUploadedImages((prev) => [...prev, { file, result }]);
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label htmlFor="campaign-id" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Campaign ID (Optional)
          </label>
          <input
            id="campaign-id"
            type="text"
            value={campaignId}
            onChange={(e) => setCampaignId(e.target.value)}
            placeholder="Enter campaign ID"
            className="w-full min-h-[44px] px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="campaign-name" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Campaign Name (Optional)
          </label>
          <input
            id="campaign-name"
            type="text"
            value={campaignName}
            onChange={(e) => setCampaignName(e.target.value)}
            placeholder="Enter campaign name"
            className="w-full min-h-[44px] px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 md:p-12 text-center transition-colors min-h-[200px] flex flex-col items-center justify-center ${
          isDragging
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50"
        }`}
      >
        <input
          type="file"
          id="image-upload"
          onChange={handleFileSelect}
          accept="image/*"
          className="hidden"
          disabled={uploading}
        />
        <label
          htmlFor="image-upload"
          className={`cursor-pointer ${uploading ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <div className="space-y-4">
            <div className="text-5xl md:text-6xl">🖼️</div>
            <div>
              <p className="text-lg md:text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
                {uploading ? "Uploading..." : "Drag & drop campaign images here"}
              </p>
              <p className="text-sm md:text-base text-slate-600 dark:text-slate-300 mb-4">
                or click to browse
              </p>
              <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400">
                Supports PNG, JPG, JPEG, GIF, WebP
              </p>
            </div>
          </div>
        </label>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {uploadedImages.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Uploaded Images ({uploadedImages.length})
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {uploadedImages.map((item, idx) => (
              <div
                key={idx}
                className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden bg-white dark:bg-slate-800"
              >
                <img
                  src={URL.createObjectURL(item.file)}
                  alt={`Uploaded ${idx + 1}`}
                  className="w-full h-48 object-cover"
                />
                <div className="p-4">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                    {item.file.name}
                  </p>
                  {item.result.visual_elements && (
                    <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                      {item.result.visual_elements.length} elements detected
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

