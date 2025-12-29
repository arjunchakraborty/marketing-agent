"use client";

import { useState } from "react";

interface PageHelpProps {
  title: string;
  description: string;
  whenToUse?: string[];
  relatedPages?: Array<{ label: string; href: string }>;
}

export function PageHelp({ title, description, whenToUse, relatedPages }: PageHelpProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mb-4 md:mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
      >
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
        <span>What is this page? When should I use it?</span>
      </button>

      {isOpen && (
        <div className="mt-3 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">{title}</h3>
          <p className="text-sm text-blue-800 dark:text-blue-200 mb-3">{description}</p>
          
          {whenToUse && whenToUse.length > 0 && (
            <div className="mb-3">
              <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">When to use:</p>
              <ul className="text-xs text-blue-800 dark:text-blue-200 space-y-1 list-disc list-inside">
                {whenToUse.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {relatedPages && relatedPages.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">Related pages:</p>
              <div className="flex flex-wrap gap-2">
                {relatedPages.map((page) => (
                  <a
                    key={page.href}
                    href={page.href}
                    className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                  >
                    {page.label}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

