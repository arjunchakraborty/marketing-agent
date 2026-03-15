"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import Link from "next/link";

export default function WorkflowDemoPage() {
  const [step, setStep] = useState(1);
  const [emailCustomizations, setEmailCustomizations] = useState({
    campaignName: "Summer Sale 2024",
    discount: "50",
    ctaText: "Shop Now",
    ctaColor: "#667eea",
    headerColor: "#667eea",
    urgencyText: "Limited Time Offer - Ends in 48 Hours!",
  });

  const sampleData = {
    csv: {
      filename: "klaviyo_campaigns.csv",
      rows: 10,
      size: "2.1 KB",
      preview: [
        { campaign: "Summer Sale 2024", openRate: "45%", revenue: "$12,500" },
        { campaign: "New Product Launch", openRate: "45%", revenue: "$25,000" },
        { campaign: "Flash Sale", openRate: "50%", revenue: "$60,000" },
      ],
    },
    images: {
      count: 5,
      campaigns: ["CAMP001", "CAMP003", "CAMP005", "CAMP007", "CAMP010"],
      analysis: {
        visualElements: 12,
        dominantColors: ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"],
        ctas: 8,
      },
    },
    experiment: {
      campaignsAnalyzed: 5,
      imagesAnalyzed: 5,
      correlations: 3,
      insights: [
        "Campaigns with red CTAs show 15% higher conversion",
        "Hero images with product focus increase open rates by 8%",
        "Clearance campaigns with urgency indicators drive 20% more revenue",
      ],
    },
    campaign: {
      segments: ["High Value Customers", "Price Sensitive Shoppers"],
      estimatedReach: 4500,
      expectedUplift: "+12.5%",
    },
  };

  return (
    <AppShell>
      <div className="w-full max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Workflow Demo with Sample Data
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300">
            See how the workflow processes sample campaign data and images to generate insights.
          </p>
        </div>

        {/* Step Navigation */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {[1, 2, 3, 4].map((stepNum) => (
              <div key={stepNum} className="flex-1 flex items-center">
                <div className="flex flex-col items-center flex-1">
                  <button
                    onClick={() => setStep(stepNum)}
                    className={`w-12 h-12 rounded-full flex items-center justify-center font-semibold transition-colors ${
                      step === stepNum
                        ? "bg-blue-600 text-white"
                        : step > stepNum
                        ? "bg-green-500 text-white"
                        : "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                    }`}
                  >
                    {step > stepNum ? "✓" : stepNum}
                  </button>
                  <p className="mt-2 text-xs font-medium text-slate-600 dark:text-slate-400">
                    Step {stepNum}
                  </p>
                </div>
                {stepNum < 4 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
                      step > stepNum ? "bg-green-500" : "bg-slate-200 dark:bg-slate-700"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm">
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                  Step 1: Upload Sales Data
                </h2>
                <p className="text-slate-600 dark:text-slate-300">
                  Sample CSV file uploaded and processed
                </p>
              </div>

              <div className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="font-semibold text-green-900 dark:text-green-100">Upload Successful</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <p><strong>File:</strong> {sampleData.csv.filename}</p>
                  <p><strong>Rows:</strong> {sampleData.csv.rows} campaigns</p>
                  <p><strong>Size:</strong> {sampleData.csv.size}</p>
                  <p><strong>Status:</strong> Ingested into database</p>
                </div>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">Sample Campaign Data Preview</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-slate-100 dark:bg-slate-700">
                      <tr>
                        <th className="px-4 py-2 text-left">Campaign</th>
                        <th className="px-4 py-2 text-left">Open Rate</th>
                        <th className="px-4 py-2 text-left">Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sampleData.csv.preview.map((row, idx) => (
                        <tr key={idx} className="border-t border-slate-200 dark:border-slate-700">
                          <td className="px-4 py-2">{row.campaign}</td>
                          <td className="px-4 py-2">{row.openRate}</td>
                          <td className="px-4 py-2">{row.revenue}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                  Step 2: Upload Campaign Images
                </h2>
                <p className="text-slate-600 dark:text-slate-300">
                  Sample campaign images analyzed for visual elements
                </p>
              </div>

              <div className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="font-semibold text-green-900 dark:text-green-100">Images Analyzed</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <p><strong>Images:</strong> {sampleData.images.count} campaign images</p>
                  <p><strong>Campaigns:</strong> {sampleData.images.campaigns.join(", ")}</p>
                  <p><strong>Visual Elements:</strong> {sampleData.images.analysis.visualElements} detected</p>
                  <p><strong>CTAs Found:</strong> {sampleData.images.analysis.ctas}</p>
                </div>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">Dominant Colors Detected</h4>
                <div className="flex gap-2 flex-wrap">
                  {sampleData.images.analysis.dominantColors.map((color, idx) => (
                    <div
                      key={idx}
                      className="w-16 h-16 rounded-lg border-2 border-slate-300 dark:border-slate-600"
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                  Step 3: Analyze & Correlate
                </h2>
                <p className="text-slate-600 dark:text-slate-300">
                  Campaign strategy experiment results
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                    {sampleData.experiment.campaignsAnalyzed}
                  </div>
                  <div className="text-sm text-blue-700 dark:text-blue-300">Campaigns Analyzed</div>
                </div>
                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                  <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                    {sampleData.experiment.imagesAnalyzed}
                  </div>
                  <div className="text-sm text-purple-700 dark:text-purple-300">Images Analyzed</div>
                </div>
                <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
                  <div className="text-2xl font-bold text-orange-900 dark:text-orange-100">
                    {sampleData.experiment.correlations}
                  </div>
                  <div className="text-sm text-orange-700 dark:text-orange-300">Correlations Found</div>
                </div>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">Key Insights</h4>
                <ul className="space-y-2">
                  {sampleData.experiment.insights.map((insight, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <Link
                href="/dashboard#campaign-strategy-experiment"
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                View Full Experiment Results →
              </Link>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                  Step 4: Create Targeted Campaign & Preview Email
                </h2>
                <p className="text-slate-600 dark:text-slate-300">
                  Use insights to build your next campaign and preview the email before sending
                </p>
              </div>

              <div className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="font-semibold text-green-900 dark:text-green-100">Campaign Ready</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <p><strong>Target Segments:</strong> {sampleData.campaign.segments.join(", ")}</p>
                  <p><strong>Estimated Reach:</strong> {sampleData.campaign.estimatedReach.toLocaleString()} customers</p>
                  <p><strong>Expected Uplift:</strong> {sampleData.campaign.expectedUplift}</p>
                </div>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-3">Campaign Strategy</h4>
                <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
                  <li>• Use red CTA buttons (15% higher conversion)</li>
                  <li>• Include product-focused hero images (8% open rate boost)</li>
                  <li>• Add urgency indicators for clearance campaigns (20% revenue increase)</li>
                  <li>• Target high-value customers with exclusive offers</li>
                </ul>
              </div>

              {/* Email Preview Section */}
              <div className="p-6 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-4">Email Preview</h4>
                <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">
                  Preview how your email will look to customers. Customize the content below and see it update in real-time.
                </p>

                {/* Quick Customization */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Campaign Name
                    </label>
                    <input
                      type="text"
                      value={emailCustomizations.campaignName}
                      onChange={(e) =>
                        setEmailCustomizations({ ...emailCustomizations, campaignName: e.target.value })
                      }
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Discount %
                    </label>
                    <input
                      type="number"
                      value={emailCustomizations.discount}
                      onChange={(e) =>
                        setEmailCustomizations({ ...emailCustomizations, discount: e.target.value })
                      }
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      CTA Button Text
                    </label>
                    <input
                      type="text"
                      value={emailCustomizations.ctaText}
                      onChange={(e) =>
                        setEmailCustomizations({ ...emailCustomizations, ctaText: e.target.value })
                      }
                      className="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      CTA Color
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={emailCustomizations.ctaColor}
                        onChange={(e) =>
                          setEmailCustomizations({ ...emailCustomizations, ctaColor: e.target.value })
                        }
                        className="w-12 h-10 border border-slate-300 dark:border-slate-600 rounded-lg cursor-pointer"
                      />
                      <input
                        type="text"
                        value={emailCustomizations.ctaColor}
                        onChange={(e) =>
                          setEmailCustomizations({ ...emailCustomizations, ctaColor: e.target.value })
                        }
                        className="flex-1 px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                      />
                    </div>
                  </div>
                </div>

                {/* Email Preview */}
                <div className="border-2 border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                  <div className="bg-slate-100 dark:bg-slate-700 px-4 py-2 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <span className="ml-2 text-xs text-slate-600 dark:text-slate-300">Email Preview</span>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-900 p-4 overflow-auto max-h-[500px]">
                    <iframe
                      srcDoc={`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            background: linear-gradient(135deg, ${emailCustomizations.headerColor} 0%, #764ba2 100%);
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
            background-color: ${emailCustomizations.ctaColor};
            color: #ffffff;
            text-decoration: none;
            padding: 18px 40px;
            border-radius: 8px;
            font-size: 20px;
            font-weight: bold;
            margin: 30px 0;
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
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🎉 ${emailCustomizations.campaignName}</h1>
            <p>Your favorite brands at unbeatable prices</p>
        </div>
        <img src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&h=300&fit=crop" alt="Sale Banner" class="hero-image" />
        <div class="content">
            <h2>Don't Miss Out!</h2>
            <p>Get ready for the biggest sale of the season. Shop now and save up to ${emailCustomizations.discount}% on all your favorite items!</p>
            <div class="discount-badge">${emailCustomizations.discount}% OFF</div>
            <a href="#" class="cta-button">${emailCustomizations.ctaText} →</a>
            <div class="urgency">
                <p>⏰ ${emailCustomizations.urgencyText}</p>
            </div>
        </div>
        <div class="footer">
            <p><strong>Your Brand Name</strong></p>
            <p>123 Main Street, City, State 12345</p>
            <p><a href="#" style="color: #fff;">Unsubscribe</a> | <a href="#" style="color: #fff;">Privacy Policy</a></p>
        </div>
    </div>
</body>
</html>
                      `}
                      className="w-full border-0"
                      style={{ minHeight: "400px" }}
                      title="Email Preview"
                    />
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <div className="flex gap-3">
                    <Link
                      href="/campaigns/demo"
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-center"
                    >
                      Create Demo Campaign →
                    </Link>
                    <Link
                      href="/campaigns/email-preview"
                      className="flex-1 px-4 py-2 border border-blue-600 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-center"
                    >
                      Full Email Builder →
                    </Link>
                  </div>
                  <Link
                    href="/campaigns/target"
                    className="block w-full px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-center"
                  >
                    Create Your Own Campaign →
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="mt-8 flex justify-between">
            <button
              onClick={() => setStep(Math.max(1, step - 1))}
              disabled={step === 1}
              className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 disabled:opacity-50"
            >
              ← Previous
            </button>
            <button
              onClick={() => setStep(Math.min(4, step + 1))}
              disabled={step === 4}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Next →
            </button>
          </div>
        </div>

        <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">Try It Yourself</h3>
          <p className="text-sm text-blue-800 dark:text-blue-200 mb-4">
            Sample data files are available in <code className="bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">/sample_data/</code>
          </p>
          <div className="flex gap-2">
            <Link
              href="/workflow"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              Go to Workflow
            </Link>
            <Link
              href="/upload"
              className="px-4 py-2 border border-blue-600 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 text-sm"
            >
              Upload Sample Data
            </Link>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

