import { countryProfiles } from "@/data/countries";
import { getCountryShapeKey } from "@/lib/country-shapes";
import { getAlertStatusLabel } from "@/lib/formatters";
import { getLiveSnapshot } from "@/lib/live-snapshot";
import { getPrimaryCountryLabel, hasPublishableLeader } from "@/lib/monitoring-presentation";
import type {
  ConfidenceBand,
  LiveSnapshotBundle,
  OperationalAlertStatus,
  OperationalCountry,
  OperationalForecastRow,
  OperationalStatusSummary,
  OperationalThresholdPolicy,
} from "@/lib/types";

const curatedByIso3 = new Map(countryProfiles.map((country) => [country.iso3, country]));

const defaultThresholdPolicy: OperationalThresholdPolicy = {
  publishTopN: 10,
  publishThreshold: null,
  operatingThreshold: 0.6,
  warningThreshold: 0.5,
  alertThreshold: 0.7,
};

function slugifyCountryName(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/[_\s]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function getThresholdPolicy(bundle: LiveSnapshotBundle | null): OperationalThresholdPolicy {
  if (!bundle) {
    return defaultThresholdPolicy;
  }

  return {
    publishTopN: bundle.model_card.threshold_policy.publish_top_n,
    publishThreshold: bundle.model_card.threshold_policy.publish_threshold,
    operatingThreshold: bundle.model_card.threshold_policy.operating_threshold,
    warningThreshold: bundle.model_card.threshold_policy.warning_threshold,
    alertThreshold: bundle.model_card.threshold_policy.alert_threshold,
  };
}

function getAlertStatus(probability: number, thresholdPolicy: OperationalThresholdPolicy): OperationalAlertStatus {
  if (probability >= thresholdPolicy.alertThreshold) {
    return "alert";
  }
  if (probability >= thresholdPolicy.operatingThreshold) {
    return "operating";
  }
  if (probability >= thresholdPolicy.warningThreshold) {
    return "warning";
  }
  return "below_threshold";
}

function buildSourceNote(bundle: LiveSnapshotBundle, iso3: string): string {
  const curated = curatedByIso3.get(iso3);
  const activeProvenance =
    bundle.manifest.primary_target === "onset" ? bundle.manifest.provenance.onset : bundle.manifest.provenance.escalation;
  const structuralProvenance = bundle.manifest.provenance.structural;
  const parts = [
    `Published snapshot ${bundle.manifest.snapshot_id}.`,
    activeProvenance?.training.run_name ? `Training run ${activeProvenance.training.run_name}.` : null,
    structuralProvenance?.training.run_name ? `Structural prior ${structuralProvenance.training.run_name}.` : null,
    `Backtest leader ${bundle.backtest_summary.top_model_name ?? bundle.backtest_summary.primary_model}.`,
    curated?.sourceNote ?? null,
  ].filter(Boolean);
  return parts.join(" ");
}

function getLatestProvenanceCompletedAt(bundle: LiveSnapshotBundle | null): string | null {
  const structural = bundle?.manifest.provenance.structural;
  if (!structural) {
    return null;
  }
  const candidates = [structural.training.completed_at, structural.calibration.completed_at, structural.backtest.completed_at]
    .filter(Boolean)
    .map((value) => new Date(value));
  if (candidates.length === 0) {
    return null;
  }
  candidates.sort((left, right) => right.getTime() - left.getTime());
  return candidates[0]?.toISOString() ?? null;
}

function buildConfidenceBand(bundle: LiveSnapshotBundle, iso3: string): ConfidenceBand {
  const curated = curatedByIso3.get(iso3);
  if (curated) {
    return curated.confidenceBand;
  }
  if (bundle.status.baseline_used) {
    return "Low";
  }
  return bundle.status.lead_tie_count && bundle.status.lead_tie_count > 1 ? "Low" : "Moderate";
}

function buildChronology(bundle: LiveSnapshotBundle, iso3: string): string[] {
  const detail = bundle.country_details[iso3.toLowerCase()];
  if (detail?.chronology.length) {
    return detail.chronology;
  }

  const curated = curatedByIso3.get(iso3);
  if (curated?.timeline.length) {
    return curated.timeline.map((event) => `${event.date}: ${event.label}. ${event.summary}`);
  }

  return [`Forecast as of ${bundle.manifest.forecast_as_of}.`];
}

function buildTopDrivers(bundle: LiveSnapshotBundle, iso3: string): string[] {
  const detail = bundle.country_details[iso3.toLowerCase()];
  if (detail?.top_drivers.length) {
    return detail.top_drivers;
  }

  const curated = curatedByIso3.get(iso3);
  if (curated?.mainDrivers.length) {
    return curated.mainDrivers;
  }

  return ["No driver bundle is published for this country yet."];
}

function buildOperationalCountry(bundle: LiveSnapshotBundle, iso3: string): OperationalCountry | null {
  const forecast = bundle.forecast_snapshot.countries.find((entry) => entry.iso3 === iso3);
  if (!forecast) {
    return null;
  }

  const detail = bundle.country_details[iso3.toLowerCase()];
  const curated = curatedByIso3.get(iso3);
  const thresholdPolicy = getThresholdPolicy(bundle);
  const probability = detail?.forecast.score ?? forecast.score;
  const delta = detail?.forecast.delta ?? forecast.delta;
  const name = curated?.name ?? detail?.country_name ?? forecast.country_name;
  const region = curated?.region ?? detail?.region_name ?? forecast.region_name ?? "Unspecified";
  const summary = curated?.summary ?? detail?.summary ?? `${name} is included in the current published forecast snapshot.`;
  const executiveSummary = curated?.executiveSummary ?? detail?.summary ?? summary;
  const reportSlug = curated?.reportSlugs[0] ?? detail?.report_slug ?? null;

  return {
    iso3,
    slug: curated?.slug ?? slugifyCountryName(name),
    name,
    region,
    shapeKey: curated?.shapeKey ?? getCountryShapeKey(iso3),
    rank: detail?.forecast.rank ?? forecast.rank,
    probability,
    delta,
    forecastAsOf: detail?.forecast.forecast_as_of ?? forecast.forecast_as_of,
    publishedAt: bundle.manifest.published_at,
    freshnessTier: detail?.forecast.freshness_tier ?? forecast.freshness_tier,
    alertStatus: getAlertStatus(probability, thresholdPolicy),
    summary,
    executiveSummary,
    topDrivers: buildTopDrivers(bundle, iso3),
    chronology: buildChronology(bundle, iso3),
    reportSlug,
    dossierAvailable: Boolean(curated),
    relatedCountries: curated?.relatedCountries ?? [],
    sourceNote: buildSourceNote(bundle, iso3),
    modelName: detail?.forecast.model_name ?? bundle.model_card.model_name,
    modelVersion: detail?.forecast.model_version ?? bundle.model_card.model_version,
    targetName: detail?.forecast.target_name ?? bundle.model_card.target_name,
    horizonDays: detail?.forecast.horizon_days ?? bundle.model_card.horizon_days,
    alertType: bundle.forecast_snapshot.alert_type,
    modelStatus: bundle.model_card.model_status,
  };
}

function getBundle() {
  return getLiveSnapshot();
}

export function buildOperationalStatusSummaryFromSnapshot(snapshot: ReturnType<typeof getBundle>): OperationalStatusSummary {
  const bundle = snapshot.bundle;
  const thresholdPolicy = getThresholdPolicy(bundle);
  const baselineDelta = bundle?.backtest_summary.baseline_deltas[0] ?? null;

  return {
    sourceKind: snapshot.source_kind,
    status: snapshot.status.status,
    freshnessTier: snapshot.status.freshness_tier,
    publishedAt: snapshot.status.published_at,
    forecastAsOf: snapshot.status.forecast_as_of,
    baselineUsed: snapshot.status.baseline_used ?? false,
    coverageCount: snapshot.status.coverage_count ?? bundle?.forecast_snapshot.coverage_count ?? 0,
    leadCountryIso3: snapshot.status.lead_country_iso3,
    leadCountryName: snapshot.status.lead_country_name,
    leadTieCount: snapshot.status.lead_tie_count ?? 0,
    message: snapshot.status.message,
    predictionFile: snapshot.status.prediction_file,
    predictedConflict:
      snapshot.status.predicted_conflict ??
      bundle?.forecast_snapshot.predicted_conflict ??
      bundle?.manifest.predicted_conflict ??
      null,
    primaryTarget:
      snapshot.status.primary_target ?? bundle?.forecast_snapshot.primary_target ?? bundle?.model_card.primary_target ?? "escalation",
    alertType:
      snapshot.status.alert_type ?? bundle?.forecast_snapshot.alert_type ?? bundle?.model_card.alert_type ?? "Monitoring Only",
    modelStatus:
      snapshot.status.model_status ?? bundle?.model_card.model_status ?? bundle?.manifest.model_status ?? "monitoring_only",
    noClearLeader:
      snapshot.status.no_clear_leader ??
      bundle?.forecast_snapshot.no_clear_leader ??
      bundle?.manifest.no_clear_leader ??
      false,
    thresholdPolicy,
    modelName: bundle?.model_card.model_name ?? "unavailable",
    modelVersion: bundle?.model_card.model_version ?? "unavailable",
    primaryModel: bundle?.backtest_summary.primary_model ?? "unavailable",
    baselineModel: bundle?.backtest_summary.baseline_model ?? null,
    topModelName: bundle?.backtest_summary.top_model_name ?? null,
    calibrationMethod: bundle?.backtest_summary.calibration_method ?? null,
    deltaPrAuc: baselineDelta?.delta_pr_auc ?? null,
    deltaRocAuc: baselineDelta?.delta_roc_auc ?? null,
    deltaF1: baselineDelta?.delta_f1 ?? null,
    deltaBrierScore: baselineDelta?.delta_brier_score ?? null,
    publishThreshold:
      snapshot.status.publish_threshold ??
      bundle?.backtest_summary.publish_threshold ??
      bundle?.model_card.threshold_policy.publish_threshold ??
      null,
    episodeRecall: bundle?.backtest_summary.episode_recall ?? bundle?.model_card.metrics.episode_recall ?? null,
    falseAlertsPerTrueAlert:
      bundle?.backtest_summary.false_alerts_per_true_alert ?? bundle?.model_card.metrics.false_alerts_per_true_alert ?? null,
    recallAt5: bundle?.backtest_summary.recall_at_5 ?? bundle?.model_card.metrics.recall_at_5 ?? null,
    recallAt10: bundle?.backtest_summary.recall_at_10 ?? bundle?.model_card.metrics.recall_at_10 ?? null,
    noClearLeaderRate:
      bundle?.backtest_summary.no_clear_leader_rate ?? bundle?.model_card.metrics.no_clear_leader_rate ?? null,
    structuralPriorActive: Boolean(
      bundle?.manifest.provenance.structural &&
        (snapshot.status.primary_target ?? bundle?.manifest.primary_target ?? bundle?.model_card.primary_target) === "onset",
    ),
    structuralPriorRunName: bundle?.manifest.provenance.structural?.training.run_name ?? null,
    structuralPriorModelName: bundle?.manifest.provenance.structural?.training.model_name ?? null,
    structuralPriorCompletedAt: getLatestProvenanceCompletedAt(bundle ?? null),
  };
}

export function getOperationalStatusSummary(): OperationalStatusSummary {
  return buildOperationalStatusSummaryFromSnapshot(getBundle());
}

export function buildOperationalCountriesFromSnapshot(snapshot: ReturnType<typeof getBundle>): OperationalCountry[] {
  if (!snapshot.bundle) {
    return [];
  }

  return snapshot.bundle.forecast_snapshot.countries
    .map((country) => buildOperationalCountry(snapshot.bundle!, country.iso3))
    .filter((country): country is OperationalCountry => country !== null)
    .sort((left, right) => left.rank - right.rank || right.probability - left.probability || left.name.localeCompare(right.name));
}

export function getOperationalCountries(): OperationalCountry[] {
  return buildOperationalCountriesFromSnapshot(getBundle());
}

export function getOperationalCountryBySlug(slug: string): OperationalCountry | undefined {
  return getOperationalCountries().find((country) => country.slug === slug);
}

export function getLeadCountry(): OperationalCountry | undefined {
  return getOperationalCountries()[0];
}

export function getLeadCountries(limit = 2): OperationalCountry[] {
  return getOperationalCountries().slice(0, limit);
}

export function getLiveStripCountries(limit = 8): OperationalCountry[] {
  return getOperationalCountries().slice(0, limit);
}

export function getOperationalForecastRows(): OperationalForecastRow[] {
  return getOperationalCountries().map((country) => ({
    slug: country.slug,
    iso3: country.iso3,
    country: country.name,
    region: country.region,
    rank: country.rank,
    probability: country.probability,
    delta: country.delta,
    alertStatus: country.alertStatus,
    alertType: country.alertType,
    freshnessTier: country.freshnessTier,
    forecastAsOf: country.forecastAsOf,
    topDrivers: country.topDrivers,
  }));
}

export function getStatusLeadLabel(): string {
  const status = getOperationalStatusSummary();
  const label = getPrimaryCountryLabel(status);
  if (!status.leadCountryName) {
    return label === "Lead Country" ? "No published lead country" : "No current watch";
  }
  if (!hasPublishableLeader(status)) {
    return `${status.leadCountryName} / Monitoring only`;
  }
  return `${status.leadCountryName} / ${getAlertStatusLabel(getLeadCountry()?.alertStatus ?? "below_threshold")}`;
}

export function getLeadConfidenceBand(): ConfidenceBand {
  const snapshot = getBundle();
  const lead = getLeadCountry();
  if (!snapshot.bundle || !lead) {
    return "Low";
  }
  return buildConfidenceBand(snapshot.bundle, lead.iso3);
}
