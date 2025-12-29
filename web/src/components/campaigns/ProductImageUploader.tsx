"use client";

import { useState, useRef } from "react";

interface ProductImage {
  product_id: string;
  image_url: string;
  alt_text?: string;
  file?: File;
}

interface ProductImageUploaderProps {
  products?: string[];
  onImagesChange: (images: ProductImage[]) => void;
  initialImages?: ProductImage[];
}

export function ProductImageUploader({
  products = [],
  onImagesChange,
  initialImages = [],
}: ProductImageUploaderProps) {
  const [productImages, setProductImages] = useState<ProductImage[]>(initialImages);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    const newImages: ProductImage[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!file.type.startsWith("image/")) continue;

      // Create preview URL
      const imageUrl = URL.createObjectURL(file);
      const productId = products[i] || `PROD${String(i + 1).padStart(3, "0")}`;

      newImages.push({
        product_id: productId,
        image_url: imageUrl,
        alt_text: file.name.replace(/\.[^/.]+$/, ""),
        file,
      });
    }

    const updatedImages = [...productImages, ...newImages];
    setProductImages(updatedImages);
    onImagesChange(updatedImages);
    setUploading(false);

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleRemoveImage = (index: number) => {
    const updatedImages = productImages.filter((_, i) => i !== index);
    setProductImages(updatedImages);
    onImagesChange(updatedImages);
  };

  const handleProductIdChange = (index: number, productId: string) => {
    const updatedImages = [...productImages];
    updatedImages[index] = { ...updatedImages[index], product_id: productId };
    setProductImages(updatedImages);
    onImagesChange(updatedImages);
  };

  const handleAltTextChange = (index: number, altText: string) => {
    const updatedImages = [...productImages];
    updatedImages[index] = { ...updatedImages[index], alt_text: altText };
    setProductImages(updatedImages);
    onImagesChange(updatedImages);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Product Images
        </label>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {uploading ? "Uploading..." : "Add Images"}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {productImages.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {productImages.map((img, index) => (
            <div
              key={index}
              className="relative p-4 border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800"
            >
              <button
                type="button"
                onClick={() => handleRemoveImage(index)}
                className="absolute top-2 right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                aria-label="Remove image"
              >
                ×
              </button>

              <div className="mb-3">
                <img
                  src={img.image_url}
                  alt={img.alt_text || `Product ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg"
                />
              </div>

              <div className="space-y-2">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Product ID
                  </label>
                  {products.length > 0 ? (
                    <select
                      value={img.product_id}
                      onChange={(e) => handleProductIdChange(index, e.target.value)}
                      className="w-full px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    >
                      {products.map((prod) => (
                        <option key={prod} value={prod}>
                          {prod}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={img.product_id}
                      onChange={(e) => handleProductIdChange(index, e.target.value)}
                      placeholder="Product ID"
                      className="w-full px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    />
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Alt Text
                  </label>
                  <input
                    type="text"
                    value={img.alt_text || ""}
                    onChange={(e) => handleAltTextChange(index, e.target.value)}
                    placeholder="Image description"
                    className="w-full px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {productImages.length === 0 && (
        <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-8 text-center">
          <p className="text-slate-600 dark:text-slate-400 mb-4">
            No product images added yet
          </p>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
          >
            Upload Product Images
          </button>
        </div>
      )}
    </div>
  );
}

