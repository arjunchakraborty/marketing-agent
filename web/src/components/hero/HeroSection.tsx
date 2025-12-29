import Link from "next/link";

export function HeroSection() {
  return (
    <section className="relative w-full py-12 md:py-20 lg:py-28 px-4 md:px-6 overflow-hidden">
      <div className="mx-auto max-w-7xl">
        <div className="text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 dark:text-slate-100 mb-4 md:mb-6">
            Marketing Intelligence
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
              Powered by AI
            </span>
          </h1>
          <p className="text-lg md:text-xl text-slate-600 dark:text-slate-300 mb-8 md:mb-12 max-w-3xl mx-auto px-4">
            Unlock the power of data-driven marketing with intelligent analytics, 
            campaign optimization, and automated insights.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto min-h-[44px] px-8 py-3 bg-slate-900 text-white rounded-full font-semibold text-base hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200 transition-colors shadow-lg"
            >
              Get Started
            </Link>
            <Link
              href="/upload"
              className="w-full sm:w-auto min-h-[44px] px-8 py-3 border-2 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100 rounded-full font-semibold text-base hover:border-slate-400 dark:hover:border-slate-500 transition-colors"
            >
              Upload Data
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

