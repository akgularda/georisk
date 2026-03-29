import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-3xl px-5 py-24 text-center sm:px-8">
      <p className="terminal-label text-accent">Not found</p>
      <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em] text-foreground">The requested page is not available.</h1>
      <p className="mt-4 text-base leading-8 text-muted">Return to the homepage or move into the forecast explorer.</p>
      <div className="mt-8 flex justify-center gap-3">
        <Link href="/" className="rounded-md border border-border bg-surface-strong px-5 py-3 text-sm font-semibold text-foreground">
          Theater desk
        </Link>
        <Link href="/forecasts" className="rounded-md border border-border bg-surface-muted px-5 py-3 text-sm font-semibold text-foreground">
          Forecast board
        </Link>
      </div>
    </div>
  );
}
