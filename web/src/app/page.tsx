import { HeroSection } from "@/components/hero/HeroSection";
import { FeaturesGrid } from "@/components/hero/FeaturesGrid";
import { BenefitsSection } from "@/components/hero/BenefitsSection";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-slate-200 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <HeroSection />
      <FeaturesGrid />
      <BenefitsSection />
    </div>
  );
}
