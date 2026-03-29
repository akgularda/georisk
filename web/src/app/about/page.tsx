import { SectionHeading } from "@/components/section-heading";

export const metadata = {
  title: "About",
};

export default function AboutPage() {
  return (
    <div className="dashboard-canvas pb-20 md:pb-8">
      <section className="shell-panel border-x-0 border-t-0 px-8 py-10 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <SectionHeading
            eyebrow="About"
            title="A published warning surface, not a speculative dashboard"
            description="GeoRisk is for readers who want ranked forecasts, visible caveats, and explicit publication state. The goal is not to simulate authority but to disclose what the model currently says and how trustworthy the publication state is."
          />
        </div>
      </section>
      <section className="mx-auto max-w-7xl p-8">
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="shell-card p-7 text-sm leading-8 text-muted">
          <p>
            The platform combines event, narrative, humanitarian, and macro context to publish a country-ranked forecast snapshot.
            It is designed to show the next problematic country even if nobody touches the site for a long time, provided that the
            publication pipeline keeps producing snapshots.
          </p>
          <p className="mt-5">
            The visual system is intentionally severe. It follows a command-center structure because the site should read like a
            government-style operational bulletin, not like a consumer analytics product or a speculative AI dashboard.
          </p>
          <p className="mt-5">
            The most important object on the site is the published country forecast itself. Ranking, probability, freshness, and
            provenance support that focal point. They are not decorative widgets.
          </p>
        </section>

        <aside className="shell-card p-7">
          <p className="command-eyebrow text-[#ff8f82]">Editorial Rules</p>
          <ul className="mt-4 space-y-3 text-sm leading-7 text-muted">
            <li>Freshness and fallback state stay visible on the first screen.</li>
            <li>Country pages must render for any published forecast country, not only a curated set.</li>
            <li>Probabilities are shown as probabilities, not inflated crisis scores.</li>
            <li>Methodology and backtest context remain readable from the live site.</li>
          </ul>
        </aside>
      </div>
      </section>
    </div>
  );
}
