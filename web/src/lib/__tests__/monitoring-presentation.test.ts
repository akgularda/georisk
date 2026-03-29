import assert from "node:assert/strict";
import test from "node:test";

import {
  buildMonitoringWatchItems,
  getCountryDisplaySummary,
  getPredictedConflictLabel,
  getPrimaryCountryLabel,
  getReportConflictLabel,
} from "@/lib/monitoring-presentation";
import type { OperationalCountry, OperationalStatusSummary, ReportFrontmatter } from "@/lib/types";

function buildCountry(overrides: Partial<OperationalCountry> & Pick<OperationalCountry, "iso3" | "slug" | "name">): OperationalCountry {
  return {
    iso3: overrides.iso3,
    slug: overrides.slug,
    name: overrides.name,
    region: overrides.region ?? "Region",
    shapeKey: overrides.shapeKey ?? null,
    rank: overrides.rank ?? 1,
    probability: overrides.probability ?? 0,
    delta: overrides.delta ?? 0,
    forecastAsOf: overrides.forecastAsOf ?? "2026-03-23",
    publishedAt: overrides.publishedAt ?? "2026-03-29T00:34:18.086724+00:00",
    freshnessTier: overrides.freshnessTier ?? "fresh",
    alertStatus: overrides.alertStatus ?? "below_threshold",
    summary: overrides.summary ?? `${overrides.name} summary`,
    executiveSummary: overrides.executiveSummary ?? `${overrides.name} executive summary`,
    topDrivers: overrides.topDrivers ?? [],
    chronology: overrides.chronology ?? [],
    reportSlug: overrides.reportSlug ?? null,
    dossierAvailable: overrides.dossierAvailable ?? false,
    relatedCountries: overrides.relatedCountries ?? [],
    sourceNote: overrides.sourceNote ?? "Source note",
    modelName: overrides.modelName ?? "logit",
    modelVersion: overrides.modelVersion ?? "country_week_onset_logit_30d",
    targetName: overrides.targetName ?? "country_week_onset_30d",
    horizonDays: overrides.horizonDays ?? 30,
    alertType: overrides.alertType ?? "No Clear Leader",
    modelStatus: overrides.modelStatus ?? "monitoring_only",
  };
}

function buildStatus(overrides: Partial<OperationalStatusSummary> = {}): OperationalStatusSummary {
  return {
    sourceKind: overrides.sourceKind ?? "preferred",
    status: overrides.status ?? "ok",
    freshnessTier: overrides.freshnessTier ?? "fresh",
    publishedAt: overrides.publishedAt ?? "2026-03-29T00:34:18.086724+00:00",
    forecastAsOf: overrides.forecastAsOf ?? "2026-03-23",
    baselineUsed: overrides.baselineUsed ?? false,
    coverageCount: overrides.coverageCount ?? 30,
    leadCountryIso3: overrides.leadCountryIso3 ?? "AUS",
    leadCountryName: overrides.leadCountryName ?? "Australia",
    leadTieCount: overrides.leadTieCount ?? 16,
    message: overrides.message ?? null,
    predictionFile: overrides.predictionFile ?? null,
    primaryTarget: overrides.primaryTarget ?? "onset",
    alertType: overrides.alertType ?? "No Clear Leader",
    modelStatus: overrides.modelStatus ?? "monitoring_only",
    noClearLeader: overrides.noClearLeader ?? true,
    thresholdPolicy: overrides.thresholdPolicy ?? {
      publishTopN: 10,
      publishThreshold: null,
      operatingThreshold: 0.6,
      warningThreshold: 0.5,
      alertThreshold: 0.7,
    },
    modelName: overrides.modelName ?? "logit",
    modelVersion: overrides.modelVersion ?? "country_week_onset_logit_30d",
    primaryModel: overrides.primaryModel ?? "logit",
    baselineModel: overrides.baselineModel ?? "prior_rate",
    topModelName: overrides.topModelName ?? "prior_rate",
    calibrationMethod: overrides.calibrationMethod ?? "isotonic",
    deltaPrAuc: overrides.deltaPrAuc ?? null,
    deltaRocAuc: overrides.deltaRocAuc ?? null,
    deltaF1: overrides.deltaF1 ?? null,
    deltaBrierScore: overrides.deltaBrierScore ?? null,
    publishThreshold: overrides.publishThreshold ?? null,
    episodeRecall: overrides.episodeRecall ?? null,
    falseAlertsPerTrueAlert: overrides.falseAlertsPerTrueAlert ?? null,
    recallAt5: overrides.recallAt5 ?? null,
    recallAt10: overrides.recallAt10 ?? null,
    noClearLeaderRate: overrides.noClearLeaderRate ?? null,
    structuralPriorActive: overrides.structuralPriorActive ?? true,
    structuralPriorRunName: overrides.structuralPriorRunName ?? null,
    structuralPriorModelName: overrides.structuralPriorModelName ?? null,
    structuralPriorCompletedAt: overrides.structuralPriorCompletedAt ?? null,
  };
}

function buildReport(overrides: Partial<ReportFrontmatter> & Pick<ReportFrontmatter, "title" | "slug" | "date" | "summary" | "region" | "countries">): ReportFrontmatter {
  return {
    title: overrides.title,
    slug: overrides.slug,
    date: overrides.date,
    updatedAt: overrides.updatedAt ?? `${overrides.date}T00:00:00Z`,
    authors: overrides.authors ?? ["Model Desk"],
    summary: overrides.summary,
    region: overrides.region,
    countries: overrides.countries,
    targets: overrides.targets ?? ["regional_escalation_risk"],
    horizon: overrides.horizon ?? "30d",
    tags: overrides.tags ?? ["Watch"],
    forecastVersion: overrides.forecastVersion ?? "web-demo-2026.03",
    confidenceBand: overrides.confidenceBand ?? "Moderate",
    sources: overrides.sources ?? ["ACLED"],
    heroMetric: overrides.heroMetric ?? "Watch",
    draft: overrides.draft ?? false,
    toc: overrides.toc ?? [],
  };
}

test("prioritizes report-backed countries when monitoring mode has no clear leader", () => {
  const countries = [
    buildCountry({ iso3: "AUS", slug: "australia", name: "Australia", rank: 1, probability: 0.0004 }),
    buildCountry({ iso3: "IRN", slug: "iran", name: "Iran", rank: 26 }),
    buildCountry({ iso3: "ISR", slug: "israel", name: "Israel", rank: 27 }),
    buildCountry({ iso3: "SDN", slug: "sudan", name: "Sudan", rank: 28 }),
  ];
  const reports = [
    buildReport({
      title: "Iran-Israel theater watch",
      slug: "iran-israel-escalation-watch",
      date: "2026-03-27",
      summary: "Iran and Israel now sit at the center of the theater desk.",
      region: "Middle East",
      countries: ["iran", "israel"],
    }),
    buildReport({
      title: "Sudan risk brief",
      slug: "sudan-corridor-pressure",
      date: "2026-03-26",
      summary: "Sudan remains under heavy corridor pressure.",
      region: "Africa",
      countries: ["sudan"],
    }),
  ];

  const items = buildMonitoringWatchItems(countries, reports);

  assert.deepEqual(items.map((item) => item.country.iso3), ["IRN", "ISR", "SDN", "AUS"]);
});

test("uses report-backed summary for a country page during monitoring mode", () => {
  const iran = buildCountry({
    iso3: "IRN",
    slug: "iran",
    name: "Iran",
    executiveSummary: "Generic snapshot summary",
    reportSlug: null,
  });
  const reports = [
    buildReport({
      title: "Iran-Israel theater watch",
      slug: "iran-israel-escalation-watch",
      date: "2026-03-27",
      summary: "Iran and Israel now sit at the center of the theater desk.",
      region: "Middle East",
      countries: ["iran", "israel"],
    }),
  ];

  const summary = getCountryDisplaySummary(iran, buildStatus(), reports);

  assert.equal(summary, "Iran and Israel now sit at the center of the theater desk.");
});

test("switches the primary label from lead country to current watch when monitoring", () => {
  assert.equal(getPrimaryCountryLabel(buildStatus()), "Current Watch");
  assert.equal(
    getPrimaryCountryLabel(
      buildStatus({
        alertType: "Onset Watch",
        modelStatus: "promoted",
        noClearLeader: false,
        leadTieCount: 1,
      }),
    ),
    "Lead Country",
  );
});

test("builds a multi-country predicted conflict label from report countries", () => {
  const report = buildReport({
    title: "Iran-Israel theater watch",
    slug: "iran-israel-escalation-watch",
    date: "2026-03-27",
    summary: "Iran and Israel now sit at the center of the theater desk.",
    region: "Middle East",
    countries: ["iran", "israel"],
  });

  assert.equal(getReportConflictLabel(report), "Iran / Israel");
});

test("falls back to the focus country when no report-backed conflict label exists", () => {
  const ukraine = buildCountry({
    iso3: "UKR",
    slug: "ukraine",
    name: "Ukraine",
  });

  assert.equal(getPredictedConflictLabel(null, ukraine), "Ukraine");
});
