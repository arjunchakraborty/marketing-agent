"use client";

import { useState, useCallback } from "react";
import { uploadSalesFile } from "@/lib/api";

interface FileUploaderProps {
  onUploadComplete?: (result: any) => void;
}

export function FileUploader({ onUploadComplete }: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [business, setBusiness] = useState("");

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

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        await handleFileUpload(files[0]);
      }
    },
    [business]
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        await handleFileUpload(files[0]);
      }
    },
    [business]
  );

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const result = await uploadSalesFile(file, business || undefined, true);
      setUploadResult(result);
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  return (
    <div className="w-full space-y-6">
      <div className="space-y-2">
        <label htmlFor="business" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Business Name (Optional)
        </label>
        <input
          id="business"
          type="text"
          value={business}
          onChange={(e) => setBusiness(e.target.value)}
          placeholder="Enter business name"
          className="w-full min-h-[44px] px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
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
          id="file-upload"
          onChange={handleFileSelect}
          accept=".csv,.xlsx,.xls,.json,.png,.jpg,.jpeg,.gif,.webp"
          className="hidden"
          disabled={uploading}
        />
        <label
          htmlFor="file-upload"
          className={`cursor-pointer ${uploading ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <div className="space-y-4">
            <div className="text-5xl md:text-6xl">📁</div>
            <div>
              <p className="text-lg md:text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
                {uploading ? "Uploading..." : "Drag & drop your file here"}
              </p>
              <p className="text-sm md:text-base text-slate-600 dark:text-slate-300 mb-4">
                or click to browse
              </p>
              <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400">
                Supports CSV, Excel, JSON, and Image files
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

      {uploadResult && (
        <div className="p-4 md:p-6 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
          <h3 className="text-lg font-semibold text-green-800 dark:text-green-200 mb-2">
            Upload Successful!
          </h3>
          <div className="space-y-2 text-sm text-green-700 dark:text-green-300">
            <p>
              <span className="font-semibold">File:</span> {uploadResult.filename}
            </p>
            <p>
              <span className="font-semibold">Type:</span> {uploadResult.file_type.toUpperCase()}
            </p>
            <p>
              <span className="font-semibold">Size:</span> {formatFileSize(uploadResult.file_size)}
            </p>
            {uploadResult.ingested && (
              <>
                <p>
                  <span className="font-semibold">Status:</span> {uploadResult.status}
                </p>
                {uploadResult.table_name && (
                  <p>
                    <span className="font-semibold">Table:</span> {uploadResult.table_name}
                  </p>
                )}
                {uploadResult.row_count !== undefined && (
                  <p>
                    <span className="font-semibold">Rows:</span> {uploadResult.row_count.toLocaleString()}
                  </p>
                )}
              </>
            )}
            {uploadResult.errors && uploadResult.errors.length > 0 && (
              <div className="mt-2">
                <p className="font-semibold">Errors:</p>
                <ul className="list-disc list-inside">
                  {uploadResult.errors.map((err: string, idx: number) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

