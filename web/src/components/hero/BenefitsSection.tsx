const benefits = [
  "Increase campaign ROI with data-driven insights",
  "Automate marketing workflows and reduce manual work",
  "Understand customer behavior with cohort analysis",
  "Optimize campaigns with AI-powered recommendations",
  "Track performance across all marketing channels",
];

export function BenefitsSection() {
  return (
    <section className="w-full py-12 md:py-20 px-4 md:px-6 bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900">
      <div className="mx-auto max-w-7xl">
        <h2 className="text-3xl md:text-4xl font-bold text-center text-slate-900 dark:text-slate-100 mb-8 md:mb-12">
          Why Choose Our Platform
        </h2>
        <div className="max-w-3xl mx-auto">
          <ul className="space-y-4 md:space-y-6">
            {benefits.map((benefit, index) => (
              <li
                key={index}
                className="flex items-start gap-4 p-4 md:p-6 rounded-lg bg-white dark:bg-slate-800 shadow-sm"
              >
                <span className="text-2xl">✓</span>
                <span className="text-lg md:text-xl text-slate-700 dark:text-slate-200 flex-1">
                  {benefit}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

