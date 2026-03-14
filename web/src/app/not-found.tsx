import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6">
      <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">404</h1>
      <p className="text-zinc-600 dark:text-zinc-400">This page could not be found.</p>
      <Link
        href="/"
        className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 dark:bg-violet-500 dark:hover:bg-violet-600 transition-colors"
      >
        Back to home
      </Link>
    </div>
  );
}
