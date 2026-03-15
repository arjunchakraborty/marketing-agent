const features = [
  {
    title: "Advanced Analytics",
    description: "Real-time KPI tracking, cohort analysis, and predictive forecasting",
    icon: "📊",
  },
  {
    title: "Campaign Management",
    description: "AI-powered campaign recommendations and strategy optimization",
    icon: "🎯",
  },
  {
    title: "Image Analysis",
    description: "Visual element detection and campaign image insights",
    icon: "🖼️",
  },
  {
    title: "Smart Targeting",
    description: "Audience segmentation and targeted campaign creation",
    icon: "🎨",
  },
  {
    title: "Data Ingestion",
    description: "Multi-format file uploads (CSV, Excel, JSON) with automatic processing",
    icon: "📥",
  },
  {
    title: "SQL Explorer",
    description: "Natural language to SQL conversion for custom queries",
    icon: "🔍",
  },
];

export function FeaturesGrid() {
  return (
    <section className="w-full py-12 md:py-20 px-4 md:px-6 bg-white dark:bg-slate-900">
      <div className="mx-auto max-w-7xl">
        <h2 className="text-3xl md:text-4xl font-bold text-center text-slate-900 dark:text-slate-100 mb-12 md:mb-16">
          Powerful Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="p-6 md:p-8 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:shadow-lg transition-shadow"
            >
              <div className="text-4xl md:text-5xl mb-4">{feature.icon}</div>
              <h3 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-2 md:mb-3">
                {feature.title}
              </h3>
              <p className="text-slate-600 dark:text-slate-300 text-sm md:text-base">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

