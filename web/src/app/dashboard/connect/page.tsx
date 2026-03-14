import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ConnectStorePage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Connect your Shopify store
        </h1>
        <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">
          One-time setup. We’ll sync your customers and orders for targeting.
        </p>
      </div>

      <Card className="max-w-xl border-zinc-200 dark:border-zinc-700">
        <CardHeader>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Install the app</h2>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Click below to open the Shopify App Store and install our app on your store. You’ll be asked to approve access once.
          </p>
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-200">
            <strong>Coming soon.</strong> Shopify connection is not yet available. You can still create campaigns using product data uploaded in{" "}
            <Link href="/dashboard/data-upload" className="font-medium text-amber-900 underline underline-offset-2 hover:no-underline dark:text-amber-100">
              Data upload
            </Link>.
          </div>
          <Button disabled>Connect with Shopify</Button>
        </CardContent>
      </Card>
    </div>
  );
}
