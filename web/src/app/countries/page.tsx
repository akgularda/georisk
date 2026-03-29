import { MonitorTable } from "@/components/monitor-table";
import { SectionHeading } from "@/components/section-heading";
import { getAllReports } from "@/lib/content";
import { formatProbabilityPercent } from "@/lib/formatters";
import { buildMonitoringWatchItems, getPrimaryCountryLabel, hasPublishableLeader } from "@/lib/monitoring-presentation";
import { getLeadCountry, getOperationalCountries, getOperationalStatusSummary } from "@/lib/site-data";

export const metadata = {
  title: "Countries",
};

export default async function CountriesIndexPage() {
  const countries = getOperationalCountries();
  const leadCountry = getLeadCountry();
  const status = getOperationalStatusSummary();
  const reports = await getAllReports();
  const publishableLeader = hasPublishableLeader(status);
  const watchItems = publishableLeader ? [] : buildMonitoringWatchItems(countries, reports);
  const focusCountry = publishableLeader ? leadCountry : watchItems[0]?.country ?? leadCountry;
  const focusReport = publishableLeader ? null : watchItems[0]?.report ?? null;
  const orderedCountries = publishableLeader ? countries : watchItems.map((item) => item.country);

  return (
    <div className="dashboard-canvas pb-20 md:pb-8">
      <section className="shell-panel border-x-0 border-t-0 px-8 py-10 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <SectionHeading
            eyebrow="Country monitor"
            title="Every published country in the current snapshot"
            description="The country board is no longer constrained to a curated dossier set. Any published forecast country can appear here, route here, and surface as the lead case."
          />
        </div>
      </section>

      <section className="mx-auto max-w-7xl space-y-8 p-8">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Published Countries</p>
          <p className="mt-3 text-4xl font-semibold tracking-[-0.06em] text-foreground">{countries.length}</p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">{getPrimaryCountryLabel(status)}</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">{focusCountry?.name ?? "Unavailable"}</p>
          <p className="mt-2 text-sm text-muted">
            {publishableLeader
              ? focusCountry
                ? formatProbabilityPercent(focusCountry.probability)
                : "No published lead"
              : focusReport?.title ?? "Report-backed monitoring board"}
          </p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Freshness Tier</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">{status.freshnessTier}</p>
          <p className="mt-2 text-sm text-muted">{status.message ?? "Preferred published snapshot is active."}</p>
        </div>
      </div>

      <MonitorTable countries={orderedCountries} />
      </section>
    </div>
  );
}
