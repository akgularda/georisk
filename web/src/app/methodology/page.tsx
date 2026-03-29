import Link from "next/link";
import { SectionHeading } from "@/components/section-heading";
import { formatProbabilityPercent } from "@/lib/formatters";
import { getAllMethodologyPages } from "@/lib/content";
import { getOperationalStatusSummary } from "@/lib/site-data";

export const metadata = {
  title: "Methodology",
};

export default async function MethodologyIndexPage() {
  const pages = await getAllMethodologyPages();
  const status = getOperationalStatusSummary();

  return (
    <div className="dashboard-canvas pb-20 md:pb-8">
      <section className="shell-panel border-x-0 border-t-0 px-8 py-10 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <SectionHeading
            eyebrow="Methodology"
            title="A live trust surface, not a static caveat page"
            description="The methodology route exposes current publication quality, threshold policy, and backtest standing before the reader drills into the longer reference pages."
          />
        </div>
      </section>

      <section className="mx-auto max-w-7xl space-y-8 p-8">
      <div className="grid gap-4 md:grid-cols-4">
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Primary Target</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">{status.primaryTarget}</p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Alert Type</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">{status.alertType}</p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Publish Threshold</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">
            {status.publishThreshold == null ? "Unavailable" : formatProbabilityPercent(status.publishThreshold)}
          </p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Episode Recall</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">
            {status.episodeRecall == null ? "Unavailable" : formatProbabilityPercent(status.episodeRecall)}
          </p>
        </div>
      </div>

      <div className="shell-card p-6">
        <p className="command-eyebrow text-[#ff8f82]">Current Disclosure</p>
        <p className="mt-3 max-w-4xl text-sm leading-7 text-muted">
          {status.message ?? "Preferred published snapshot is active."} The current public state is {status.alertType} on the {status.primaryTarget} target, with model status {status.modelStatus}. The site should keep this page synchronized with the actual bundle, model card, and backtest summary rather than relying on stale narrative copy.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {pages.map((page) => (
          <Link key={page.slug} href={`/methodology/${page.slug}`} className="shell-card p-6 transition-colors hover:border-primary/25 hover:bg-surface-high">
            <p className="command-eyebrow text-[#ff8f82]">{page.slug}</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-foreground">{page.title}</h2>
            <p className="mt-3 text-sm leading-7 text-muted">{page.summary}</p>
          </Link>
        ))}
      </div>
      </section>
    </div>
  );
}
