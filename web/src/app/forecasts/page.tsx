import { ForecastExplorer } from "@/components/forecast-explorer";
import { MethodologyNote } from "@/components/methodology-note";
import { SectionHeading } from "@/components/section-heading";
import { getAllReports } from "@/lib/content";
import { formatProbabilityDelta, formatProbabilityPercent } from "@/lib/formatters";
import { buildMonitoringWatchItems, getPrimaryCountryLabel, hasPublishableLeader } from "@/lib/monitoring-presentation";
import { getLeadCountry, getOperationalCountries, getOperationalForecastRows, getOperationalStatusSummary } from "@/lib/site-data";

export const metadata = {
  title: "Forecast explorer",
};

function getDisplayName(row: { name: string } | { country: string } | undefined): string {
  if (!row) {
    return "Unavailable";
  }
  return "country" in row ? row.country : row.name;
}

export default async function ForecastsPage() {
  const rawRows = getOperationalForecastRows();
  const countries = getOperationalCountries();
  const status = getOperationalStatusSummary();
  const leadCountry = getLeadCountry();
  const reports = await getAllReports();
  const publishableLeader = hasPublishableLeader(status);
  const watchItems = publishableLeader ? [] : buildMonitoringWatchItems(countries, reports);
  const monitoringOrder = new Map(watchItems.map((item, index) => [item.country.iso3, index]));
  const rows = publishableLeader
    ? rawRows
    : [...rawRows].sort((left, right) => {
        const leftIndex = monitoringOrder.get(left.iso3) ?? Number.MAX_SAFE_INTEGER;
        const rightIndex = monitoringOrder.get(right.iso3) ?? Number.MAX_SAFE_INTEGER;
        return leftIndex - rightIndex || left.rank - right.rank;
      });
  const focusRow = publishableLeader ? leadCountry : rows[0];
  const focusWatch = publishableLeader ? null : watchItems[0] ?? null;
  const focusCountryName = publishableLeader
    ? leadCountry?.name ?? "Unavailable"
    : focusWatch?.country.name ?? getDisplayName(focusRow);
  const topProbability = rows[0]?.probability ?? 0;
  const largestMove = rows.length
    ? rows.reduce((currentLargest, row) => {
        return Math.abs(row.delta) > Math.abs(currentLargest.delta) ? row : currentLargest;
      }, rows[0])
    : null;
  const regionsCovered = new Set(rows.map((row) => row.region)).size;

  return (
    <div className="dashboard-canvas pb-20 md:pb-8">
      <section className="shell-panel border-x-0 border-t-0 px-8 py-10 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <SectionHeading
            eyebrow="Forecast board"
            title="Published country rankings with exact 30-day probabilities"
            description="This surface reads only from the canonical site snapshot. It stays table-first, keeps the published probability visible, and shows threshold state instead of decorative crisis color."
          />
        </div>
      </section>

      <section className="mx-auto max-w-7xl space-y-8 p-8">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">{getPrimaryCountryLabel(status)}</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">
            {focusCountryName}
          </p>
          <p className="mt-2 text-sm text-muted">
            {publishableLeader
              ? leadCountry
                ? formatProbabilityPercent(leadCountry.probability)
                : "No published lead"
              : focusWatch?.report?.title ?? "Report-backed monitoring board"}
          </p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">{publishableLeader ? "Top Probability" : "Watch Brief"}</p>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.06em] text-foreground">
            {publishableLeader ? formatProbabilityPercent(topProbability) : focusWatch?.report?.date ?? status.forecastAsOf ?? "Unavailable"}
          </p>
          <p className="mt-2 text-sm text-muted">
            {publishableLeader
              ? status.forecastAsOf
                ? `Snapshot week ${status.forecastAsOf}`
                : "Unavailable"
              : focusWatch?.report?.summary ?? status.message ?? "Monitoring board is active."}
          </p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">{publishableLeader ? "Largest Weekly Move" : "Model State"}</p>
          <p className={publishableLeader && largestMove && largestMove.delta > 0 ? "mt-3 text-3xl font-semibold tracking-[-0.06em] text-[#ff8f82]" : "mt-3 text-3xl font-semibold tracking-[-0.06em] text-foreground"}>
            {publishableLeader ? (largestMove ? formatProbabilityDelta(largestMove.delta) : "0.00 pp") : status.modelStatus.replaceAll("_", " ")}
          </p>
          <p className="mt-2 text-sm text-muted">{publishableLeader ? largestMove?.country ?? "Unavailable" : status.alertType}</p>
        </div>
        <div className="shell-card p-5 md:col-span-3">
          <p className="command-eyebrow text-[#ff8f82]">Publication Context</p>
          <div className="mt-4 grid gap-4 md:grid-cols-4">
            <div>
              <p className="command-eyebrow">Source</p>
              <p className="mt-2 text-base font-semibold text-foreground">{status.sourceKind}</p>
            </div>
            <div>
              <p className="command-eyebrow">Coverage</p>
              <p className="mt-2 text-base font-semibold text-foreground">{status.coverageCount} countries</p>
            </div>
            <div>
              <p className="command-eyebrow">Regions</p>
              <p className="mt-2 text-base font-semibold text-foreground">{regionsCovered}</p>
            </div>
            <div>
              <p className="command-eyebrow">Backtest Leader</p>
              <p className="mt-2 text-base font-semibold text-foreground">{status.topModelName ?? "Unavailable"}</p>
            </div>
          </div>
          <p className="mt-4 text-sm leading-7 text-muted">
            {status.message ?? "Preferred published snapshot is active."}
          </p>
        </div>
      </div>

      <ForecastExplorer rows={rows} />
      <MethodologyNote />
      </section>
    </div>
  );
}
