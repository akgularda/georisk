import { AppIcon } from "@/components/app-icon";
import Link from "next/link";
import { ReportCard } from "@/components/report-card";
import { countryShapes } from "@/lib/country-shapes";
import { getAllReports } from "@/lib/content";
import { formatDateTime, formatProbabilityDelta, formatProbabilityPercent } from "@/lib/formatters";
import { buildHomepageState } from "@/lib/homepage-state";
import {
  getMonitoringHeroConflictLabel,
  getMonitoringHeroSummary,
  getPredictedConflictLabel,
  getReportConflictLabel,
} from "@/lib/monitoring-presentation";
import { getOperationalCountries, getOperationalStatusSummary } from "@/lib/site-data";

function displayConfidence(modelStatus: string, noClearLeader: boolean) {
  if (noClearLeader) {
    return "Guarded";
  }
  if (modelStatus === "promoted") {
    return "High";
  }
  return "Moderate";
}

function riskRankClass(index: number) {
  if (index < 2) {
    return "risk-rank-item-critical";
  }
  if (index < 4) {
    return "risk-rank-item-elevated";
  }
  return "risk-rank-item-neutral";
}

function targetLabel(targetName: string) {
  return targetName.replaceAll("_", " ");
}

function LeadMap({ shapeKey, title }: { shapeKey: keyof typeof countryShapes | null; title: string }) {
  const shapePath = shapeKey ? countryShapes[shapeKey] : null;

  return (
    <div className="relative flex h-72 w-72 shrink-0 items-center justify-center">
      <div className="hero-ring" />
      <div className="hero-ring hero-ring-delay-1" />
      <div className="hero-ring hero-ring-delay-2" />
      <div className="hero-map-core">
        <div className="absolute inset-0 bg-gradient-to-t from-surface via-transparent to-transparent" />
        {shapePath ? (
          <svg viewBox="0 0 360 360" className="absolute inset-[15%] h-[70%] w-[70%]" role="img" aria-label={`${title} silhouette`}>
            <path d={shapePath} className="hero-map-shape" />
          </svg>
        ) : null}
        <div className="hero-map-pin">
          <AppIcon name="location_on" className="h-12 w-12" />
        </div>
      </div>
    </div>
  );
}

export default async function HomePage() {
  const countries = getOperationalCountries();
  const status = getOperationalStatusSummary();
  const reports = await getAllReports();
  const homepage = buildHomepageState(countries, status, reports);
  const leadCountry = homepage.focusCountry;
  const leadReport = homepage.focusReport ?? reports[0];
  const recentReports = reports.slice(0, 6);
  const topCountries = homepage.watchItems;
  const heroConflictLabel =
    homepage.mode === "monitoring"
      ? getMonitoringHeroConflictLabel(leadReport, leadCountry, status.predictedConflict?.label)
      : leadCountry?.name ?? "";
  const heroSummary =
    homepage.mode === "monitoring"
      ? getMonitoringHeroSummary(leadReport, leadCountry, status.predictedConflict?.summary)
      : homepage.heroSummary;

  if (!leadCountry) {
    return (
      <div className="dashboard-canvas min-h-screen px-6 py-10">
        <section className="shell-panel mx-auto max-w-7xl p-10">
          <div className="command-hero-alert">
            <span className="command-hero-alert-dot" />
            <span>No live snapshot</span>
          </div>
          <h2 className="command-hero-title mt-6 text-foreground">NO PUBLISHED LEAD</h2>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-[rgba(218,226,253,0.78)]">
            {status.message ?? "The warning surface has no publishable country lead right now."}
          </p>
          <Link href="/status" className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-foreground hover:text-primary">
            Open status
            <AppIcon name="arrow_forward" className="h-4 w-4" />
          </Link>
        </section>
      </div>
    );
  }

  const shapeKey = leadCountry.shapeKey ?? null;

  return (
    <div className="dashboard-canvas pb-20 md:pb-8">
      <section className="shell-panel overflow-hidden border-x-0 border-t-0 px-8 py-8 lg:px-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center gap-12 lg:flex-row">
          <LeadMap shapeKey={shapeKey} title={leadCountry.name} />

          <div className="flex-1 text-center lg:text-left">
            <div className="command-hero-alert">
              <span className="command-hero-alert-dot" />
              <span>
                {homepage.mode === "monitoring"
                  ? "No publishable model lead: report-backed monitoring board"
                  : `${status.alertType}: operational lead`}
              </span>
            </div>

            {homepage.mode === "monitoring" ? (
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.24em] text-[rgba(255,143,130,0.86)]">
                Predicted Conflict
              </p>
            ) : null}

            <h1 className="command-hero-title mt-4 text-foreground">
              {(homepage.mode === "monitoring" ? heroConflictLabel : leadCountry.name).toUpperCase()}
            </h1>

            {homepage.mode === "monitoring" ? (
              <p className="mt-3 max-w-2xl text-sm uppercase tracking-[0.18em] text-[rgba(218,226,253,0.54)]">
                Primary country focus: {leadCountry.name}
              </p>
            ) : null}

            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-[rgba(218,226,253,0.82)]">
              {heroSummary}
            </p>

            <div className="mt-6 flex flex-wrap justify-center gap-4 lg:justify-start">
              <div className="command-stat-card command-stat-card-primary">
                <div className="text-[10px] uppercase tracking-[0.2em] text-[rgba(218,226,253,0.56)]">
                  {homepage.mode === "monitoring" ? "Active Watches" : "Onset Prob."}
                </div>
                <div className="font-headline mt-1 text-2xl font-bold text-primary">
                  {homepage.mode === "monitoring" ? String(topCountries.length).padStart(2, "0") : formatProbabilityPercent(leadCountry.probability)}
                </div>
              </div>
              <div className="command-stat-card command-stat-card-secondary">
                <div className="text-[10px] uppercase tracking-[0.2em] text-[rgba(218,226,253,0.56)]">
                  {homepage.mode === "monitoring" ? "Forecast As Of" : "Weekly Move"}
                </div>
                <div className="font-headline mt-1 text-2xl font-bold text-secondary">
                  {homepage.mode === "monitoring" ? leadCountry.forecastAsOf : formatProbabilityDelta(leadCountry.delta)}
                </div>
              </div>
              <div className="command-stat-card command-stat-card-tertiary">
                <div className="text-[10px] uppercase tracking-[0.2em] text-[rgba(218,226,253,0.56)]">
                  {homepage.mode === "monitoring" ? "Model State" : "Conf. Level"}
                </div>
                <div className="font-headline mt-1 text-2xl font-bold text-tertiary">
                  {homepage.mode === "monitoring" ? "Monitoring" : displayConfidence(status.modelStatus, status.noClearLeader)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl grid-cols-1 gap-8 p-8 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-4">
          <div className="flex items-center justify-between">
            <h2 className="font-headline text-xl font-bold uppercase tracking-tight text-foreground">
              {homepage.mode === "monitoring" ? "Current Watchlist" : "Risk Rank"}
            </h2>
            <span className="bg-surface-high px-2 py-1 text-[10px] font-medium uppercase tracking-[0.2em] text-[rgba(218,226,253,0.6)]">
              {homepage.mode === "monitoring" ? "Report-led" : "Live Updates"}
            </span>
          </div>

          <div className="space-y-3">
            {topCountries.map((item, index) => (
              <Link key={item.country.iso3} href={`/countries/${item.country.slug}`} className={`risk-rank-item group ${riskRankClass(index)}`}>
                <div className="flex items-center space-x-4">
                  <span className="font-headline text-lg font-bold text-[rgba(218,226,253,0.42)] group-hover:text-[rgba(218,226,253,0.82)]">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <div className="text-sm font-bold text-foreground">{item.country.name}</div>
                    <div className="text-[10px] uppercase tracking-[0.16em] text-[rgba(218,226,253,0.56)]">
                      {homepage.mode === "monitoring"
                        ? item.report?.title ?? targetLabel(item.country.targetName)
                        : targetLabel(item.country.targetName)}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={homepage.mode === "monitoring" ? "font-headline text-sm font-bold leading-5 text-foreground" : "font-headline text-lg font-bold text-foreground"}>
                    {homepage.mode === "monitoring"
                      ? item.report ? getReportConflictLabel(item.report) : item.country.name
                      : formatProbabilityPercent(item.country.probability)}
                  </div>
                  <div className={item.country.delta > 0 ? "text-[8px] font-bold uppercase text-error" : "text-[8px] font-bold uppercase text-[rgba(218,226,253,0.58)]"}>
                    {homepage.mode === "monitoring" ? "Current watch" : `${formatProbabilityDelta(item.country.delta)} Trend`}
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <Link
            href="/forecasts"
            className="inline-flex w-full items-center justify-center border border-[rgba(69,70,77,0.22)] bg-surface-low px-4 py-4 text-xs font-bold uppercase tracking-[0.22em] text-foreground transition-colors hover:bg-surface-high"
          >
            View Full Risk Matrix
          </Link>
        </div>

        <div className="space-y-6 lg:col-span-8">
          <div className="flex items-center justify-between">
            <h2 className="font-headline text-xl font-bold uppercase tracking-tight text-foreground">Recent Intelligence Reports</h2>
            <div className="flex items-center space-x-2">
              <button className="p-1 text-[rgba(218,226,253,0.6)] hover:text-foreground" aria-label="Filter reports">
                <AppIcon name="filter_list" className="h-5 w-5" />
              </button>
              <button className="p-1 text-[rgba(218,226,253,0.6)] hover:text-foreground" aria-label="Grid view">
                <AppIcon name="grid_view" className="h-5 w-5" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {recentReports.map((report) => (
              <ReportCard key={report.slug} report={report} />
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-8 pb-10">
        <div className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
          <div className="shell-card p-6">
            <div className="command-eyebrow text-primary">Command Notes</div>
            <div className="mt-4 space-y-3 text-sm leading-7 text-[rgba(218,226,253,0.76)]">
              <p>Primary target: {status.primaryTarget}</p>
              <p>Publication state: {status.alertType}</p>
              <p>Model status: {status.modelStatus}</p>
              <p>Published source: {status.sourceKind}</p>
              <p>Published at: {status.publishedAt ? formatDateTime(status.publishedAt) : "Unavailable"}</p>
              <p>Freshness tier: {status.freshnessTier}</p>
              <p>Lead tie count: {status.leadTieCount}</p>
            </div>
            {leadReport ? (
              <Link href={`/reports/${leadReport.slug}`} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-foreground hover:text-primary">
                {homepage.mode === "monitoring" ? "Read lead watch brief" : "Read priority brief"}
                <AppIcon name="arrow_forward" className="h-4 w-4" />
              </Link>
            ) : null}
          </div>

          <div className="shell-card p-6">
            <div className="command-eyebrow text-primary">Lead Monitoring Snapshot</div>
            <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-[rgba(218,226,253,0.56)]">
                  {homepage.mode === "monitoring" ? "Predicted Conflict" : "Country"}
                </div>
                <div className="mt-2 text-lg font-semibold text-foreground">
                  {homepage.mode === "monitoring" ? heroConflictLabel : leadCountry.name}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-[rgba(218,226,253,0.56)]">
                  {homepage.mode === "monitoring" ? "Watch Basis" : "Probability"}
                </div>
                <div className="mt-2 text-lg font-semibold text-foreground">
                  {homepage.mode === "monitoring"
                    ? leadReport?.title ?? "Current watch"
                    : formatProbabilityPercent(leadCountry.probability)}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-[rgba(218,226,253,0.56)]">
                  {homepage.mode === "monitoring" ? "Latest Brief" : "Weekly Move"}
                </div>
                <div className="mt-2 text-lg font-semibold text-foreground">
                  {homepage.mode === "monitoring"
                    ? (leadReport ? leadReport.date : leadCountry.forecastAsOf)
                    : formatProbabilityDelta(leadCountry.delta)}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-[rgba(218,226,253,0.56)]">Forecast As Of</div>
                <div className="mt-2 text-lg font-semibold text-foreground">{leadCountry.forecastAsOf}</div>
              </div>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <div>
                <div className="command-eyebrow text-primary">Top Drivers</div>
                <ul className="mt-4 space-y-3 text-sm leading-7 text-[rgba(218,226,253,0.76)]">
                  {leadCountry.topDrivers.slice(0, 4).map((driver, index) => (
                    <li key={driver}>
                      <span className="mr-3 font-headline font-bold text-foreground">{String(index + 1).padStart(2, "0")}</span>
                      {driver}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="command-eyebrow text-primary">Chronology</div>
                <div className="mt-4 space-y-3 text-sm leading-7 text-[rgba(218,226,253,0.76)]">
                  {leadCountry.chronology.slice(0, 4).map((event, index) => (
                    <p key={event}>
                      <span className="mr-3 font-headline font-bold text-foreground">{String(index + 1).padStart(2, "0")}</span>
                      {event}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
