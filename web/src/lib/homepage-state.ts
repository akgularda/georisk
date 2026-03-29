import type { OperationalCountry, OperationalStatusSummary, ReportFrontmatter } from "@/lib/types";
import { buildMonitoringWatchItems, findReportForCountry, hasPublishableLeader } from "@/lib/monitoring-presentation";

export interface HomepageWatchItem {
  country: OperationalCountry;
  report: ReportFrontmatter | null;
  reason: string;
}

export interface HomepageState {
  mode: "empty" | "lead" | "monitoring";
  focusCountry: OperationalCountry | null;
  focusReport: ReportFrontmatter | null;
  heroSummary: string;
  watchItems: HomepageWatchItem[];
}

export function buildHomepageState(
  countries: OperationalCountry[],
  status: OperationalStatusSummary,
  reports: ReportFrontmatter[],
): HomepageState {
  if (countries.length === 0) {
    return {
      mode: "empty",
      focusCountry: null,
      focusReport: null,
      heroSummary: status.message ?? "No published snapshot is available.",
      watchItems: [],
    };
  }

  if (!hasPublishableLeader(status)) {
    const monitoringItems = buildMonitoringWatchItems(countries, reports);
    const focusItem = monitoringItems[0] ?? null;
    return {
      mode: "monitoring",
      focusCountry: focusItem?.country ?? countries[0] ?? null,
      focusReport: focusItem?.report ?? null,
      heroSummary: focusItem?.report?.summary ?? focusItem?.country.executiveSummary ?? countries[0]?.executiveSummary ?? "",
      watchItems: monitoringItems.slice(0, 5),
    };
  }

  const leadCountry = countries[0];
  const leadReport = findReportForCountry(leadCountry, reports);
  return {
    mode: "lead",
    focusCountry: leadCountry,
    focusReport: leadReport,
    heroSummary: leadCountry.executiveSummary,
    watchItems: countries.slice(0, 5).map((country) => ({
      country,
      report: findReportForCountry(country, reports),
      reason: country.topDrivers[0] ?? country.executiveSummary,
    })),
  };
}
