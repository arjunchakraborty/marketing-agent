"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import Link from "next/link";

export default function EmailPreviewPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<"full" | "simple">("full");
  const [customizations, setCustomizations] = useState({
    campaignName: "Summer Sale 2024",
    discount: "50",
    ctaText: "Shop Now",
    ctaColor: "#667eea",
    headerColor: "#667eea",
    urgencyText: "Limited Time Offer - Ends in 48 Hours!",
  });

  const fullTemplate = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${customizations.campaignName}</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, Helvetica, sans-serif;
            background-color: #f4f4f4;
        }
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }
        .header {
            background: linear-gradient(135deg, ${customizations.headerColor} 0%, #764ba2 100%);
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 {
            color: #ffffff;
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }
        .header p {
            color: #ffffff;
            margin: 10px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }
        .hero-image {
            width: 100%;
            max-width: 600px;
            height: auto;
            display: block;
        }
        .content {
            padding: 40px 30px;
            text-align: center;
        }
        .content h2 {
            color: #333333;
            font-size: 32px;
            margin: 0 0 20px 0;
            font-weight: bold;
        }
        .content p {
            color: #666666;
            font-size: 18px;
            line-height: 1.6;
            margin: 0 0 30px 0;
        }
        .discount-badge {
            background-color: #ff6b6b;
            color: #ffffff;
            font-size: 48px;
            font-weight: bold;
            padding: 20px;
            border-radius: 10px;
            display: inline-block;
            margin: 20px 0;
        }
        .cta-button {
            display: inline-block;
            background-color: ${customizations.ctaColor};
            color: #ffffff;
            text-decoration: none;
            padding: 18px 40px;
            border-radius: 8px;
            font-size: 20px;
            font-weight: bold;
            margin: 30px 0;
            transition: background-color 0.3s;
        }
        .cta-button:hover {
            opacity: 0.9;
        }
        .products {
            background-color: #f8f9fa;
            padding: 40px 30px;
        }
        .products h3 {
            color: #333333;
            font-size: 24px;
            margin: 0 0 30px 0;
            text-align: center;
        }
        .product-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        .product-item {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .product-item img {
            width: 100%;
            max-width: 150px;
            height: auto;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .product-item h4 {
            color: #333333;
            font-size: 18px;
            margin: 0 0 10px 0;
        }
        .product-item .price {
            color: ${customizations.ctaColor};
            font-size: 20px;
            font-weight: bold;
            margin: 10px 0;
        }
        .product-item .old-price {
            color: #999999;
            text-decoration: line-through;
            font-size: 16px;
        }
        .urgency {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
        }
        .urgency p {
            color: #856404;
            font-size: 18px;
            font-weight: bold;
            margin: 0;
        }
        .footer {
            background-color: #333333;
            color: #ffffff;
            padding: 30px;
            text-align: center;
            font-size: 14px;
        }
        .footer a {
            color: #ffffff;
            text-decoration: underline;
        }
        .social-proof {
            background-color: #e8f5e9;
            padding: 20px;
            margin: 30px 0;
            border-radius: 8px;
            text-align: center;
        }
        .social-proof p {
            color: #2e7d32;
            font-style: italic;
            margin: 0;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🎉 ${customizations.campaignName}</h1>
            <p>Your favorite brands at unbeatable prices</p>
        </div>
        <img src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&h=300&fit=crop" alt="Sale Banner" class="hero-image" />
        <div class="content">
            <h2>Don't Miss Out!</h2>
            <p>Get ready for the biggest sale of the season. Shop now and save up to ${customizations.discount}% on all your favorite items!</p>
            <div class="discount-badge">${customizations.discount}% OFF</div>
            <a href="#" class="cta-button">${customizations.ctaText} →</a>
            <div class="urgency">
                <p>⏰ ${customizations.urgencyText}</p>
            </div>
            <div class="social-proof">
                <p>"Best sale of the year! I saved over $200!" - Sarah M., Verified Customer</p>
            </div>
        </div>
        <div class="products">
            <h3>Featured Products</h3>
            <div class="product-grid">
                <div class="product-item">
                    <img src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=150&h=150&fit=crop" alt="Product 1" />
                    <h4>Premium Watch</h4>
                    <div class="price">$149.99</div>
                    <div class="old-price">$299.99</div>
                </div>
                <div class="product-item">
                    <img src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=150&h=150&fit=crop" alt="Product 2" />
                    <h4>Wireless Headphones</h4>
                    <div class="price">$79.99</div>
                    <div class="old-price">$159.99</div>
                </div>
                <div class="product-item">
                    <img src="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=150&h=150&fit=crop" alt="Product 3" />
                    <h4>Running Shoes</h4>
                    <div class="price">$89.99</div>
                    <div class="old-price">$179.99</div>
                </div>
                <div class="product-item">
                    <img src="https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?w=150&h=150&fit=crop" alt="Product 4" />
                    <h4>Designer Bag</h4>
                    <div class="price">$199.99</div>
                    <div class="old-price">$399.99</div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 30px;">
                <a href="#" class="cta-button">View All Products →</a>
            </div>
        </div>
        <div class="footer">
            <p><strong>Your Brand Name</strong></p>
            <p>123 Main Street, City, State 12345</p>
            <p><a href="#">Unsubscribe</a> | <a href="#">Email Preferences</a> | <a href="#">Privacy Policy</a></p>
        </div>
    </div>
</body>
</html>
  `;

  const simpleTemplate = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${customizations.campaignName}</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, Helvetica, sans-serif;
            background-color: #f4f4f4;
        }
        .email-wrapper {
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
        }
        .header {
            background-color: ${customizations.headerColor};
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 {
            color: #ffffff;
            margin: 0;
            font-size: 28px;
        }
        .banner-image {
            width: 100%;
            height: 250px;
            object-fit: cover;
            display: block;
        }
        .content {
            padding: 40px 30px;
        }
        .content h2 {
            color: #333;
            font-size: 26px;
            margin: 0 0 15px 0;
        }
        .content p {
            color: #666;
            font-size: 16px;
            line-height: 1.6;
            margin: 0 0 25px 0;
        }
        .cta-button {
            display: inline-block;
            background-color: ${customizations.ctaColor};
            color: #ffffff;
            text-decoration: none;
            padding: 15px 35px;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
            margin: 20px 0;
        }
        .footer {
            background-color: #333;
            color: #fff;
            padding: 20px;
            text-align: center;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="header">
            <h1>🎉 ${customizations.campaignName}</h1>
        </div>
        <img src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&h=250&fit=crop" alt="Sale Banner" class="banner-image" />
        <div class="content">
            <h2>Save Up to ${customizations.discount}% Off!</h2>
            <p>Don't miss our biggest sale of the year. Shop now and get amazing discounts on all your favorite products.</p>
            <p><strong>${customizations.urgencyText}</strong></p>
            <div style="text-align: center;">
                <a href="#" class="cta-button">${customizations.ctaText} →</a>
            </div>
        </div>
        <div class="footer">
            <p>Your Brand Name | <a href="#" style="color: #fff;">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
  `;

  const currentTemplate = selectedTemplate === "full" ? fullTemplate : simpleTemplate;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(currentTemplate);
    alert("Email HTML copied to clipboard!");
  };

  const downloadHTML = () => {
    const blob = new Blob([currentTemplate], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `email_template_${selectedTemplate}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <AppShell>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Campaigns", href: "/campaigns/demo" },
          { label: "Email Preview" },
        ]}
      />

      <div className="w-full max-w-7xl mx-auto">
        <div className="mb-6 md:mb-8">
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2 md:mb-3">
            Email Preview & Builder
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300">
            Customize and preview your email template before sending to customers.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Customization Panel */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                Customize Email
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Template Style
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSelectedTemplate("full")}
                      className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                        selectedTemplate === "full"
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300"
                      }`}
                    >
                      Full Template
                    </button>
                    <button
                      onClick={() => setSelectedTemplate("simple")}
                      className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                        selectedTemplate === "simple"
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300"
                      }`}
                    >
                      Simple Template
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Campaign Name
                  </label>
                  <input
                    type="text"
                    value={customizations.campaignName}
                    onChange={(e) =>
                      setCustomizations({ ...customizations, campaignName: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Discount Percentage
                  </label>
                  <input
                    type="number"
                    value={customizations.discount}
                    onChange={(e) =>
                      setCustomizations({ ...customizations, discount: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    CTA Button Text
                  </label>
                  <input
                    type="text"
                    value={customizations.ctaText}
                    onChange={(e) =>
                      setCustomizations({ ...customizations, ctaText: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    CTA Button Color
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={customizations.ctaColor}
                      onChange={(e) =>
                        setCustomizations({ ...customizations, ctaColor: e.target.value })
                      }
                      className="w-16 h-10 border border-slate-300 dark:border-slate-600 rounded-lg cursor-pointer"
                    />
                    <input
                      type="text"
                      value={customizations.ctaColor}
                      onChange={(e) =>
                        setCustomizations({ ...customizations, ctaColor: e.target.value })
                      }
                      className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Header Color
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={customizations.headerColor}
                      onChange={(e) =>
                        setCustomizations({ ...customizations, headerColor: e.target.value })
                      }
                      className="w-16 h-10 border border-slate-300 dark:border-slate-600 rounded-lg cursor-pointer"
                    />
                    <input
                      type="text"
                      value={customizations.headerColor}
                      onChange={(e) =>
                        setCustomizations({ ...customizations, headerColor: e.target.value })
                      }
                      className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Urgency Message
                  </label>
                  <textarea
                    value={customizations.urgencyText}
                    onChange={(e) =>
                      setCustomizations({ ...customizations, urgencyText: e.target.value })
                    }
                    rows={2}
                    className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={copyToClipboard}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Copy HTML
                </button>
                <button
                  onClick={downloadHTML}
                  className="flex-1 px-4 py-2 border border-blue-600 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                >
                  Download HTML
                </button>
              </div>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">💡 Tips</h3>
              <ul className="text-sm text-slate-600 dark:text-slate-300 space-y-1 list-disc list-inside">
                <li>Preview updates in real-time as you customize</li>
                <li>Test on mobile devices before sending</li>
                <li>Replace image URLs with your own hosted images</li>
                <li>Update all links before sending to customers</li>
              </ul>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Email Preview
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => window.open("", "_blank")?.document.write(currentTemplate)}
                    className="px-3 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
                  >
                    Open in New Tab
                  </button>
                </div>
              </div>

              <div className="border-2 border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                <div className="bg-slate-100 dark:bg-slate-700 px-4 py-2 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="ml-2 text-xs text-slate-600 dark:text-slate-300">
                    Email Preview
                  </span>
                </div>
                <div className="bg-slate-50 dark:bg-slate-900 p-4 overflow-auto max-h-[800px]">
                  <iframe
                    srcDoc={currentTemplate}
                    className="w-full border-0"
                    style={{ minHeight: "600px" }}
                    title="Email Preview"
                  />
                </div>
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800 p-4">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Next Steps
              </h3>
              <ol className="text-sm text-blue-800 dark:text-blue-200 space-y-1 list-decimal list-inside">
                <li>Customize the email using the controls on the left</li>
                <li>Preview how it looks in the preview panel</li>
                <li>Copy or download the HTML code</li>
                <li>Paste into your email service (Klaviyo, Mailchimp, etc.)</li>
                <li>Replace image URLs and links with your actual content</li>
                <li>Send test email before finalizing</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

