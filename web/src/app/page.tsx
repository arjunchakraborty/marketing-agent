import { HeroSection } from "@/components/hero/HeroSection";
import { FeaturesGrid } from "@/components/hero/FeaturesGrid";
import { BenefitsSection } from "@/components/hero/BenefitsSection";
import Link from "next/link";

export default function Home() {
  const quickActions = [
    {
      title: "View Dashboard",
      description: "See your analytics and KPIs",
      href: "/dashboard",
      icon: "📊",
      color: "bg-blue-500 hover:bg-blue-600",
    },
    {
      title: "Create Campaign",
      description: "Launch a new targeted campaign",
      href: "/campaigns/target",
      icon: "🎯",
      color: "bg-green-500 hover:bg-green-600",
    },
    {
      title: "Try Demo",
      description: "Explore with sample data",
      href: "/campaigns/demo",
      icon: "✨",
      color: "bg-purple-500 hover:bg-purple-600",
    },
    {
      title: "Upload Data",
      description: "Import your sales data",
      href: "/upload",
      icon: "📤",
      color: "bg-orange-500 hover:bg-orange-600",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-slate-200 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <HeroSection />
      
      {/* Quick Actions Section */}
      <section className="w-full py-8 md:py-12 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-2xl md:text-3xl font-bold text-center text-slate-900 dark:text-slate-100 mb-6 md:mb-8">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            {quickActions.map((action) => (
              <Link
                key={action.href}
                href={action.href}
                className="group relative p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-all hover:-translate-y-1"
              >
                <div className={`w-12 h-12 ${action.color} rounded-lg flex items-center justify-center text-2xl mb-4 transition-transform group-hover:scale-110`}>
                  {action.icon}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                  {action.title}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {action.description}
                </p>
                <div className="mt-4 flex items-center text-sm font-medium text-blue-600 dark:text-blue-400">
                  Get started
                  <svg
                    className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <FeaturesGrid />
      <BenefitsSection />
    </div>
  );
}
