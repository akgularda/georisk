import type { OperationalCountry, OperationalStatusSummary, ReportFrontmatter } from "@/lib/types";

export interface MonitoringWatchItem {
  country: OperationalCountry;
  report: ReportFrontmatter | null;
  reason: string;
}

function normalizeToken(value: string): string {
  return value.trim().toLowerCase().replace(/[_\s]+/g, "-");
}

function matchesCountryToken(country: OperationalCountry, token: string): boolean {
  const normalized = normalizeToken(token);
  return (
    normalized === country.iso3.toLowerCase() ||
    normalized === country.slug.toLowerCase() ||
    normalized === normalizeToken(country.name)
  );
}

function findCountryForToken(token: string, countries: OperationalCountry[]): OperationalCountry | undefined {
  return countries.find((country) => matchesCountryToken(country, token));
}

function toDisplayToken(token: string): string {
  return normalizeToken(token)
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function reportMatchesCountry(report: ReportFrontmatter, country: OperationalCountry): boolean {
  if (country.reportSlug && report.slug === country.reportSlug) {
    return true;
  }
  return report.countries.some((token) => matchesCountryToken(country, token));
}

export function getReportsForCountry(country: OperationalCountry, reports: ReportFrontmatter[]): ReportFrontmatter[] {
  return reports.filter((report) => reportMatchesCountry(report, country));
}

export function findReportForCountry(country: OperationalCountry, reports: ReportFrontmatter[]): ReportFrontmatter | null {
  return getReportsForCountry(country, reports)[0] ?? null;
}

export function getReportConflictLabel(report: ReportFrontmatter): string {
  const tokens = [...new Set(report.countries.map((country) => normalizeToken(country)).filter(Boolean))];
  if (tokens.length === 0) {
    return report.region;
  }
  return tokens.map(toDisplayToken).join(" / ");
}

export function getPredictedConflictLabel(
  report: ReportFrontmatter | null,
  fallbackCountry: OperationalCountry | null | undefined,
): string {
  if (report) {
    return getReportConflictLabel(report);
  }
  return fallbackCountry?.name ?? "Unavailable";
}

export function hasPublishableLeader(status: OperationalStatusSummary): boolean {
  return status.modelStatus === "promoted" && !status.noClearLeader && status.leadTieCount <= 1;
}

export function getPrimaryCountryLabel(status: OperationalStatusSummary): string {
  return hasPublishableLeader(status) ? "Lead Country" : "Current Watch";
}

export function buildMonitoringWatchItems(
  countries: OperationalCountry[],
  reports: ReportFrontmatter[],
): MonitoringWatchItem[] {
  const items: MonitoringWatchItem[] = [];
  const seen = new Set<string>();

  for (const report of reports) {
    for (const token of report.countries) {
      const country = findCountryForToken(token, countries);
      if (!country || seen.has(country.iso3)) {
        continue;
      }
      seen.add(country.iso3);
      items.push({
        country,
        report,
        reason: report.summary,
      });
    }
  }

  for (const country of countries) {
    if (seen.has(country.iso3)) {
      continue;
    }
    seen.add(country.iso3);
    items.push({
      country,
      report: findReportForCountry(country, reports),
      reason: country.topDrivers[0] ?? country.executiveSummary,
    });
  }

  return items;
}

export function getCountryDisplaySummary(
  country: OperationalCountry,
  status: OperationalStatusSummary,
  reports: ReportFrontmatter[],
): string {
  if (hasPublishableLeader(status)) {
    return country.executiveSummary;
  }
  return findReportForCountry(country, reports)?.summary ?? country.executiveSummary;
}
