import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CountryPulseGraphic } from "@/components/country-pulse-graphic";
import { MethodologyNote } from "@/components/methodology-note";
import { ReportCard } from "@/components/report-card";
import {
  formatDate,
  formatDateTime,
  formatProbabilityBps,
  formatProbabilityDelta,
  formatProbabilityPercent,
  getAlertStatusClasses,
  getAlertStatusLabel,
} from "@/lib/formatters";
import { getAllReports } from "@/lib/content";
import { getOperationalCountries, getOperationalCountryBySlug, getOperationalStatusSummary } from "@/lib/site-data";
import {
  findMonitoringWatchItem,
  getCountryDisplaySummary,
  getMonitoringHeroConflictLabel,
  getMonitoringWatchRank,
  getPredictedConflictLabel,
  getReportsForCountry,
  hasPublishableLeader,
} from "@/lib/monitoring-presentation";

interface CountryPageProps {
  params: Promise<{ slug: string }>;
}

export const dynamicParams = false;

export async function generateStaticParams() {
  return getOperationalCountries().map((country) => ({ slug: country.slug }));
}

export async function generateMetadata({ params }: CountryPageProps): Promise<Metadata> {
  const { slug } = await params;
  const country = getOperationalCountryBySlug(slug);
  if (!country) {
    return {};
  }
  const reports = await getAllReports();
  const status = getOperationalStatusSummary();

  return {
    title: `${country.name} forecast`,
    description: getCountryDisplaySummary(country, status, reports),
  };
}

export default async function CountryPage({ params }: CountryPageProps) {
  const { slug } = await params;
  const country = getOperationalCountryBySlug(slug);
  const status = getOperationalStatusSummary();

  if (!country) {
    notFound();
  }

  const reports = await getAllReports();
  const relatedReports = getReportsForCountry(country, reports);
  const displaySummary = getCountryDisplaySummary(country, status, reports);
  const monitoringMode = !hasPublishableLeader(status);
  const primaryReport = relatedReports[0] ?? null;
  const conflictLabel = monitoringMode
    ? getMonitoringHeroConflictLabel(primaryReport, country, status.predictedConflict?.label)
    : getPredictedConflictLabel(primaryReport, country);
  const monitoringWatchRank = monitoringMode ? getMonitoringWatchRank(country, getOperationalCountries(), reports) : null;
  const monitoringWatchItem = monitoringMode ? findMonitoringWatchItem(country, getOperationalCountries(), reports) : null;
  const displaySourceNote = monitoringMode
    ? "Report-led monitoring keeps this country visible while the model remains in no-clear-leader mode. Signals synthesize event, narrative, trade, shipping, governance, and humanitarian layers into a theater-oriented risk read."
    : country.sourceNote;
  const statusChipLabel = monitoringMode ? "Current watch" : getAlertStatusLabel(country.alertStatus);
  const statusChipClasses = monitoringMode
    ? "border-[#f06758]/35 bg-[#261214] text-[#f5b0aa]"
    : getAlertStatusClasses(country.alertStatus);

  return (
    <div className="dashboard-canvas pb-20 md:pb-8">
      <section className="shell-panel border-x-0 border-t-0 px-8 py-10 lg:px-12">
        <div className="mx-auto max-w-7xl grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <div className="shell-card p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="command-eyebrow text-[#ff8f82]">{country.region} / {country.iso3}</p>
              {monitoringMode ? (
                <p className="mt-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-[rgba(255,143,130,0.82)]">
                  Predicted conflict: {conflictLabel}
                </p>
              ) : null}
              <h2 className="font-headline mt-4 text-5xl font-bold tracking-[-0.07em] text-foreground sm:text-6xl">{country.name.toUpperCase()}</h2>
            </div>
            <div className={`inline-flex rounded-full border px-4 py-2 text-[0.72rem] font-semibold uppercase tracking-[0.18em] ${statusChipClasses}`}>
              {statusChipLabel}
            </div>
          </div>

          <p className="mt-5 max-w-3xl text-base leading-8 text-foreground">{displaySummary}</p>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">{displaySourceNote}</p>

          <div className="mt-6 grid gap-4 sm:grid-cols-4">
            <div className="command-panel-inset p-4">
              <p className="command-eyebrow">{monitoringMode ? "Watch Rank" : "Rank"}</p>
              <p className="mt-3 text-3xl font-semibold tracking-[-0.06em] text-foreground">
                {monitoringMode ? String(monitoringWatchRank ?? 0).padStart(2, "0") : String(country.rank).padStart(2, "0")}
              </p>
            </div>
            <div className="command-panel-inset p-4">
              <p className="command-eyebrow">{monitoringMode ? "Predicted Conflict" : "30d Probability"}</p>
              <p className={monitoringMode ? "mt-3 text-2xl font-semibold leading-tight text-foreground" : "mt-3 text-3xl font-semibold tracking-[-0.06em] text-foreground"}>
                {monitoringMode ? conflictLabel : formatProbabilityPercent(country.probability)}
              </p>
              <p className="mt-2 text-sm text-muted">
                {monitoringMode ? `Primary country focus: ${country.name}` : formatProbabilityBps(country.probability)}
              </p>
            </div>
            <div className="command-panel-inset p-4">
              <p className="command-eyebrow">{monitoringMode ? "Latest Brief" : "Weekly Move"}</p>
              <p className={monitoringMode ? "mt-3 text-2xl font-semibold leading-tight text-foreground" : country.delta > 0 ? "mt-3 text-3xl font-semibold tracking-[-0.06em] text-[#ff8f82]" : "mt-3 text-3xl font-semibold tracking-[-0.06em] text-foreground"}>
                {monitoringMode ? (primaryReport ? formatDate(primaryReport.date) : "Live snapshot") : formatProbabilityDelta(country.delta)}
              </p>
              {monitoringMode ? <p className="mt-2 text-sm text-muted">{primaryReport?.title ?? monitoringWatchItem?.reason ?? "Monitoring route"}</p> : null}
            </div>
            <div className="command-panel-inset p-4">
              <p className="command-eyebrow">Forecast Window</p>
              <p className="mt-3 text-3xl font-semibold tracking-[-0.06em] text-foreground">{country.horizonDays}d</p>
              <p className="mt-2 text-sm text-muted">Snapshot week {country.forecastAsOf}</p>
            </div>
          </div>
        </div>

        <div className="grid gap-6">
          <CountryPulseGraphic
            country={country.shapeKey}
            iso3={country.iso3}
            title={country.name}
            label={country.name}
            size="dossier"
            className="command-panel-inset"
          />
          <div className="shell-card p-6">
            <p className="command-eyebrow text-[#ff8f82]">Publication Metadata</p>
            <div className="mt-4 grid gap-x-6 gap-y-4 sm:grid-cols-2">
              <div className="min-w-0">
                <p className="command-eyebrow">Published</p>
                <p className="mt-2 text-sm font-semibold text-foreground">{formatDateTime(country.publishedAt)}</p>
              </div>
              <div className="min-w-0">
                <p className="command-eyebrow">Freshness</p>
                <p className="mt-2 text-sm font-semibold uppercase tracking-[0.18em] text-foreground">{country.freshnessTier}</p>
              </div>
              <div className="min-w-0">
                <p className="command-eyebrow">Model</p>
                <p className="mt-2 text-sm font-semibold leading-6 text-foreground [overflow-wrap:anywhere]">{country.modelVersion}</p>
              </div>
              <div className="min-w-0">
                <p className="command-eyebrow">Target</p>
                <p className="mt-2 text-sm font-semibold leading-6 text-foreground [overflow-wrap:anywhere]">{country.targetName}</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-7 text-muted">
              System status: {status.message ?? "Preferred published snapshot is active."}
            </p>
          </div>
        </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl grid gap-6 p-8 xl:grid-cols-[0.95fr_1.05fr_0.86fr]">
        <div className="shell-card p-6">
          <p className="command-eyebrow text-[#ff8f82]">Top Drivers</p>
          <div className="mt-4 space-y-4">
            {country.topDrivers.slice(0, 5).map((driver, index) => (
              <div key={driver} className="command-panel-inset p-4">
                <p className="command-eyebrow">{`Driver ${String(index + 1).padStart(2, "0")}`}</p>
                <p className="mt-3 text-sm leading-7 text-muted">{driver}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="shell-card p-6">
          <p className="command-eyebrow text-[#ff8f82]">Chronology</p>
          <div className="mt-4 space-y-4">
            {country.chronology.map((event, index) => (
              <div key={event} className="border-b border-border/60 pb-4 last:border-b-0 last:pb-0">
                <p className="command-eyebrow">{String(index + 1).padStart(2, "0")}</p>
                <p className="mt-2 text-sm leading-7 text-muted">{event}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="shell-card p-6">
            <p className="command-eyebrow text-[#ff8f82]">Related Reporting</p>
            <div className="mt-4 grid gap-4">
              {relatedReports.length > 0 ? (
                relatedReports.map((report) => <ReportCard key={report.slug} report={report} />)
              ) : (
                <div className="command-panel-inset p-5 text-sm leading-7 text-muted">
                  No dedicated report is attached to this country route yet. The forecast remains visible because the published snapshot includes it.
                </div>
              )}
            </div>
          </div>

          <div className="shell-card p-6">
            <p className="command-eyebrow text-[#ff8f82]">Dossier Coverage</p>
            <p className="mt-3 text-sm leading-7 text-muted">
              {country.dossierAvailable
                ? "This country also has curated dossier context in the repository."
                : "This route is rendered directly from the published forecast snapshot because no curated dossier exists yet."}
            </p>
            {country.relatedCountries.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {country.relatedCountries.map((relatedCountry) => (
                  <span key={relatedCountry} className="inline-flex rounded-full border border-border px-3 py-1 text-[0.7rem] uppercase tracking-[0.18em] text-muted">
                    {relatedCountry}
                  </span>
                ))}
              </div>
            ) : null}
          </div>

          <MethodologyNote compact />

          <Link href="/forecasts" className="inline-flex text-sm font-semibold text-foreground hover:text-primary">
            {"Return to forecast board ->"}
          </Link>
        </div>
      </section>
    </div>
  );
}
