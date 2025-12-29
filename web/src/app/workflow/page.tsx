"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { PageHelp } from "@/components/common/PageHelp";
import { FileUploader } from "@/components/upload/FileUploader";
import { ImageUploader } from "@/components/campaigns/ImageUploader";
import { TargetCampaignBuilder } from "@/components/campaigns/TargetCampaignBuilder";
import Link from "next/link";

type WorkflowStep = "upload-data" | "upload-images" | "analyze" | "create-campaign";

export default function WorkflowPage() {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>("upload-data");
  const [uploadedData, setUploadedData] = useState(false);
  const [uploadedImages, setUploadedImages] = useState(false);

  const steps = [
    {
      id: "upload-data" as WorkflowStep,
      title: "1. Upload Sales Data",
      description: "Upload campaign performance data (CSV, Excel, JSON)",
      component: (
        <FileUploader
          onUploadComplete={() => {
            setUploadedData(true);
            setTimeout(() => setCurrentStep("upload-images"), 1500);
          }}
        />
      ),
    },
    {
      id: "upload-images" as WorkflowStep,
      title: "2. Upload Campaign Images",
      description: "Upload campaign email images for visual analysis",
      component: (
        <ImageUploader
          onUploadComplete={() => {
            setUploadedImages(true);
            setTimeout(() => setCurrentStep("analyze"), 1500);
          }}
        />
      ),
    },
    {
      id: "analyze" as WorkflowStep,
      title: "3. Analyze & Correlate",
      description: "Run campaign strategy experiment to find insights",
      component: (
        <div className="space-y-4">
          <div className="p-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
              Ready to Analyze
            </h3>
            <p className="text-sm text-blue-700 dark:text-blue-300 mb-4">
              Now that you've uploaded your data and images, you can run a campaign strategy experiment
              to correlate visual elements with performance metrics.
            </p>
            <Link
              href="/dashboard#campaign-strategy-experiment"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go to Campaign Strategy Experiment →
            </Link>
          </div>
          <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
            <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">What happens next:</h4>
            <ul className="text-sm text-slate-600 dark:text-slate-300 space-y-1 list-disc list-inside">
              <li>Query your top-performing campaigns using SQL or natural language</li>
              <li>Analyze images to extract visual elements (CTAs, colors, layout)</li>
              <li>Correlate visual elements with performance metrics</li>
              <li>Get insights on what makes campaigns successful</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      id: "create-campaign" as WorkflowStep,
      title: "4. Create Targeted Campaign",
      description: "Use insights to build your next campaign",
      component: (
        <div className="space-y-4">
          <div className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
              Create Your Campaign
            </h3>
            <p className="text-sm text-green-700 dark:text-green-300 mb-4">
              Use the insights from your analysis to create targeted campaigns with the right
              audience segments and objectives.
            </p>
          </div>
          <TargetCampaignBuilder />
        </div>
      ),
    },
  ];

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);
  const currentStepData = steps[currentStepIndex];

  return (
    <AppShell>
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Workflow" },
        ]}
      />
      
      <div className="w-full max-w-6xl mx-auto">
        {/* Workflow Header */}
        <div className="mb-6 md:mb-8">
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2 md:mb-3">
            Campaign Workflow
          </h1>
          <p className="text-sm md:text-base text-slate-600 dark:text-slate-300 mb-4">
            Follow this step-by-step workflow to upload data, analyze campaigns, and create targeted campaigns.
          </p>

          <PageHelp
            title="Guided Workflow Experience"
            description="This is a guided, step-by-step experience that walks you through the complete campaign creation process. All steps are integrated here for convenience."
            whenToUse={[
              "You're new to the platform and want guidance",
              "You want to complete the full workflow in one place",
              "You prefer a structured, step-by-step approach"
            ]}
            relatedPages={[
              { label: "Upload Data (Direct)", href: "/upload" },
              { label: "Campaign Images (Direct)", href: "/campaigns/images" },
              { label: "Create Campaign (Direct)", href: "/campaigns/target" },
              { label: "Workflow Demo", href: "/workflow/demo" }
            ]}
          />

          <div className="p-3 md:p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <p className="text-xs md:text-sm text-green-800 dark:text-green-200">
              <strong>✨ Recommended for first-time users:</strong> This workflow guides you through all steps. You can also access each step individually from the sidebar if you prefer.
            </p>
          </div>
        </div>

        {/* Step Progress Indicator */}
        <div className="mb-6 md:mb-8">
          <div className="flex items-center justify-between mb-3 md:mb-4 overflow-x-auto pb-2">
            {steps.map((step, index) => {
              const isActive = step.id === currentStep;
              const isCompleted = index < currentStepIndex;
              const isAccessible = index <= currentStepIndex || (index === 1 && uploadedData) || (index === 2 && uploadedImages);

              return (
                <div key={step.id} className="flex-1 flex items-center">
                  <div className="flex flex-col items-center flex-1">
                    <button
                      onClick={() => isAccessible && setCurrentStep(step.id)}
                      disabled={!isAccessible}
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors ${
                        isActive
                          ? "bg-blue-600 text-white"
                          : isCompleted
                          ? "bg-green-500 text-white"
                          : isAccessible
                          ? "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed"
                      }`}
                    >
                      {isCompleted ? "✓" : index + 1}
                    </button>
                    <div className="mt-2 text-center">
                      <p
                        className={`text-xs font-medium ${
                          isActive
                            ? "text-blue-600 dark:text-blue-400"
                            : isCompleted
                            ? "text-green-600 dark:text-green-400"
                            : "text-slate-500 dark:text-slate-400"
                        }`}
                      >
                        {step.title.split(" ")[0]} {step.title.split(" ")[1]}
                      </p>
                    </div>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`flex-1 h-1 mx-2 ${
                        isCompleted ? "bg-green-500" : "bg-slate-200 dark:bg-slate-700"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Current Step Content */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 md:p-8 shadow-sm">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
              {currentStepData.title}
            </h2>
            <p className="text-slate-600 dark:text-slate-300">{currentStepData.description}</p>
          </div>

          <div className="mt-6">{currentStepData.component}</div>

          {/* Navigation Buttons */}
          <div className="mt-8 flex justify-between">
            <button
              onClick={() => {
                if (currentStepIndex > 0) {
                  setCurrentStep(steps[currentStepIndex - 1].id);
                }
              }}
              disabled={currentStepIndex === 0}
              className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← Previous
            </button>
            <button
              onClick={() => {
                if (currentStepIndex < steps.length - 1) {
                  setCurrentStep(steps[currentStepIndex + 1].id);
                }
              }}
              disabled={currentStepIndex === steps.length - 1}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        </div>

        {/* Demo Link */}
        <div className="mt-8 p-4 md:p-6 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
            See It In Action
          </h3>
          <p className="text-sm text-blue-800 dark:text-blue-200 mb-4">
            View a demo of the workflow with sample data and images to understand how everything connects.
          </p>
          <div className="flex gap-3 flex-wrap">
            <Link
              href="/workflow/demo"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Demo with Sample Data →
            </Link>
            <Link
              href="/campaigns/email-preview"
              className="px-4 py-2 border border-blue-600 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
            >
              Preview & Customize Email →
            </Link>
          </div>
        </div>

        {/* Quick Links */}
        <div className="mt-8 p-4 md:p-6 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
            Quick Links
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <Link
              href="/upload"
              className="p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-blue-500 transition-colors"
            >
              <div className="font-semibold text-slate-900 dark:text-slate-100">Upload Data</div>
              <div className="text-slate-600 dark:text-slate-400 mt-1">Upload sales/campaign files</div>
            </Link>
            <Link
              href="/campaigns/images"
              className="p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-blue-500 transition-colors"
            >
              <div className="font-semibold text-slate-900 dark:text-slate-100">Campaign Images</div>
              <div className="text-slate-600 dark:text-slate-400 mt-1">Analyze campaign visuals</div>
            </Link>
            <Link
              href="/campaigns/target"
              className="p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-blue-500 transition-colors"
            >
              <div className="font-semibold text-slate-900 dark:text-slate-100">Target Campaign</div>
              <div className="text-slate-600 dark:text-slate-400 mt-1">Create targeted campaigns</div>
            </Link>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

