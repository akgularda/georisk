import fs from "node:fs";
import path from "node:path";

import { buildLiveSnapshotStatus } from "@/lib/status";
import { getFreshnessTierFromSnapshotBounds } from "@/lib/freshness";
import type {
  FreshnessTier,
  LiveSnapshotBacktestDelta,
  LiveSnapshotBacktestSummary,
  LiveSnapshotBundle,
  LiveSnapshotCountryDetail,
  LiveSnapshotForecastCountry,
  LiveSnapshotForecastSnapshot,
  LiveSnapshotLoadResult,
  LiveSnapshotManifest,
  LiveSnapshotModelCard,
  LiveSnapshotRunProvenance,
  LiveSnapshotSourceKind,
  LiveSnapshotStatus,
} from "@/lib/types";

const defaultPreferredBundleDir = path.resolve(
  /* turbopackIgnore: true */ process.cwd(),
  "..",
  "artifacts",
  "website_publishing",
  "site_snapshot",
  "latest",
);
const defaultFallbackBundleFile = path.resolve(
  /* turbopackIgnore: true */ process.cwd(),
  "..",
  "artifacts",
  "examples",
  "website_snapshot_example.json",
);

const liveSnapshotCache = new Map<string, LiveSnapshotLoadResult>();

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asNullableString(value: unknown): string | null {
  return typeof value === "string" ? value : value == null ? null : String(value);
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function asBoolean(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => (typeof item === "string" ? item : String(item))).filter(Boolean) : [];
}

function isFreshnessTier(value: unknown): value is FreshnessTier {
  return value === "fresh" || value === "aging" || value === "stale" || value === "critical" || value === "missing";
}

interface JsonReadResult<T> {
  value: T | null;
  error: string | null;
}

function readJsonResult<T>(filePath: string): JsonReadResult<T> {
  if (!fs.existsSync(filePath)) {
    return { value: null, error: null };
  }

  try {
    return {
      value: JSON.parse(fs.readFileSync(filePath, "utf8")) as T,
      error: null,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown parse error";
    return {
      value: null,
      error: `Failed to parse ${path.basename(filePath)}: ${message}`,
    };
  }
}

function readJsonDirectory<T>(directoryPath: string): Array<{ filePath: string; value: T }> {
  if (!fs.existsSync(directoryPath) || !fs.statSync(directoryPath).isDirectory()) {
    return [];
  }

  return fs
    .readdirSync(directoryPath)
    .filter((entry) => entry.endsWith(".json"))
    .sort()
    .map((entry) => {
      const filePath = path.join(directoryPath, entry);
      return { filePath, value: readJsonResult<T>(filePath).value };
    })
    .filter((entry): entry is { filePath: string; value: T } => entry.value !== null);
}

function normalizeProvenance(value: unknown): LiveSnapshotModelCard["provenance"] {
  const normalizeRun = (run: unknown): LiveSnapshotRunProvenance => ({
    run_name: asString(isRecord(run) ? run.run_name : undefined, ""),
    artifact_path: asString(isRecord(run) ? run.artifact_path : undefined, ""),
    completed_at: asString(isRecord(run) ? run.completed_at : undefined, ""),
    model_name: asNullableString(isRecord(run) ? run.model_name : undefined),
  });

  const normalizeTarget = (target: unknown) =>
    !isRecord(target)
      ? null
      : {
          training: normalizeRun(target.training),
          calibration: normalizeRun(target.calibration),
          backtest: normalizeRun(target.backtest),
        };

  if (!isRecord(value)) {
    return { onset: null, escalation: null, structural: null };
  }

  if ("onset" in value || "escalation" in value || "structural" in value) {
    return {
      onset: normalizeTarget(value.onset),
      escalation: normalizeTarget(value.escalation),
      structural: normalizeTarget(value.structural),
    };
  }

  const legacyTarget = {
    training: normalizeRun(value.training),
    calibration: normalizeRun(value.calibration),
    backtest: normalizeRun(value.backtest),
  };

  return {
    onset: null,
    escalation: legacyTarget,
    structural: null,
  };
}

function normalizeManifest(raw: unknown): LiveSnapshotManifest | null {
  if (!isRecord(raw)) {
    return null;
  }

  return {
    schema_version: asString(raw.schema_version),
    snapshot_id: asString(raw.snapshot_id),
    published_at: asString(raw.published_at),
    fresh_until: asString(raw.fresh_until),
    stale_after: asString(raw.stale_after),
    baseline_used: asBoolean(raw.baseline_used),
    forecast_as_of: asString(raw.forecast_as_of),
    generated_at: asString(raw.generated_at),
    coverage_count: asNumber(raw.coverage_count),
    top_country_iso3: asNullableString(raw.top_country_iso3),
    top_country_name: asNullableString(raw.top_country_name),
    predicted_conflict: normalizePredictedConflict(raw.predicted_conflict, {
      iso3: asNullableString(raw.top_country_iso3),
      country_name: asNullableString(raw.top_country_name),
      target_name: asString(raw.primary_target, "escalation"),
      horizon_days: 30,
    }),
    primary_target: asString(raw.primary_target, "escalation"),
    alert_type: asString(raw.alert_type, "Monitoring Only") as LiveSnapshotManifest["alert_type"],
    model_status: asString(raw.model_status, "monitoring_only") as LiveSnapshotManifest["model_status"],
    no_clear_leader: asBoolean(raw.no_clear_leader),
    provenance: normalizeProvenance(raw.provenance),
  };
}

function normalizeModelCard(raw: unknown, manifest: LiveSnapshotManifest): LiveSnapshotModelCard | null {
  if (!isRecord(raw)) {
    return null;
  }

  const metrics = isRecord(raw.metrics) ? raw.metrics : {};
  const thresholdPolicy = isRecord(raw.threshold_policy) ? raw.threshold_policy : {};

  return {
    model_name: asString(raw.model_name),
    model_version: asString(raw.model_version),
    target_name: asString(raw.target_name, manifest.primary_target),
    horizon_days: asNumber(raw.horizon_days, 30),
    published_at: asString(raw.published_at, manifest.published_at),
    stale_after: asString(raw.stale_after, manifest.stale_after),
    baseline_used: asBoolean(raw.baseline_used, manifest.baseline_used),
    primary_target: asString(raw.primary_target, manifest.primary_target),
    alert_type: asString(raw.alert_type, manifest.alert_type) as LiveSnapshotModelCard["alert_type"],
    model_status: asString(raw.model_status, manifest.model_status) as LiveSnapshotModelCard["model_status"],
    metrics: {
      brier_score: asNumber(metrics.brier_score),
      roc_auc: asNumber(metrics.roc_auc),
      precision_at_10: asNumber(metrics.precision_at_10),
      recall_at_5: typeof metrics.recall_at_5 === "number" ? asNumber(metrics.recall_at_5) : null,
      recall_at_10: typeof metrics.recall_at_10 === "number" ? asNumber(metrics.recall_at_10) : null,
      episode_recall: typeof metrics.episode_recall === "number" ? asNumber(metrics.episode_recall) : null,
      false_alerts_per_true_alert:
        typeof metrics.false_alerts_per_true_alert === "number"
          ? asNumber(metrics.false_alerts_per_true_alert)
          : null,
      no_clear_leader_rate:
        typeof metrics.no_clear_leader_rate === "number"
          ? asNumber(metrics.no_clear_leader_rate)
          : null,
    },
    threshold_policy: {
      publish_top_n: asNumber(thresholdPolicy.publish_top_n, 0),
      publish_threshold: typeof thresholdPolicy.publish_threshold === "number" ? asNumber(thresholdPolicy.publish_threshold) : null,
      alert_threshold: asNumber(thresholdPolicy.alert_threshold, 0),
      warning_threshold: asNumber(thresholdPolicy.warning_threshold, 0),
      operating_threshold: asNumber(thresholdPolicy.operating_threshold, 0),
    },
    provenance: normalizeProvenance(raw.provenance ?? manifest.provenance),
  };
}

function resolveFreshnessTier(rawTier: unknown, manifest: LiveSnapshotManifest, now: Date): FreshnessTier {
  if (isFreshnessTier(rawTier)) {
    return rawTier;
  }

  return getFreshnessTierFromSnapshotBounds({
    publishedAt: manifest.published_at,
    freshUntil: manifest.fresh_until,
    staleAfter: manifest.stale_after,
    now,
  });
}

function normalizePredictedConflictCountry(raw: unknown) {
  const country = isRecord(raw) ? raw : {};
  return {
    iso3: asNullableString(country.iso3)?.toUpperCase() ?? null,
    country_name: asString(country.country_name),
  };
}

function normalizePredictedConflict(
  raw: unknown,
  fallback: {
    iso3: string | null;
    country_name: string | null;
    target_name: string;
    horizon_days: number;
    summary?: string | null;
    report_slug?: string | null;
  },
) {
  const predicted = isRecord(raw) ? raw : {};
  const countries = Array.isArray(predicted.countries)
    ? predicted.countries.map(normalizePredictedConflictCountry).filter((country) => country.country_name.length > 0)
    : [];

  if (countries.length === 0 && fallback.country_name) {
    countries.push({
      iso3: fallback.iso3,
      country_name: fallback.country_name,
    });
  }

  const fallbackReasonSource = fallback.summary ? "report_inputs" : fallback.country_name ? "lead_country" : "fallback";

  return {
    label:
      asString(predicted.label) ||
      countries.map((country) => country.country_name).filter(Boolean).join(" / ") ||
      fallback.country_name ||
      "No predicted conflict",
    countries,
    summary: asNullableString(predicted.summary) ?? fallback.summary ?? null,
    report_slug: asNullableString(predicted.report_slug) ?? fallback.report_slug ?? null,
    reason_source:
      (asString(predicted.reason_source) as "report_inputs" | "lead_country" | "fallback") || fallbackReasonSource,
    target_name: asString(predicted.target_name, fallback.target_name),
    horizon_days: asNumber(predicted.horizon_days, fallback.horizon_days),
  };
}

function normalizeForecastCountry(
  raw: unknown,
  manifest: LiveSnapshotManifest,
  index: number,
  now: Date,
): LiveSnapshotForecastCountry {
  const country = isRecord(raw) ? raw : {};
  return {
    iso3: asString(country.iso3).toUpperCase(),
    country_name: asString(country.country_name),
    region_name: asNullableString(country.region_name),
    score: asNumber(country.score),
    delta: asNumber(country.delta),
    forecast_as_of: asString(country.forecast_as_of, manifest.forecast_as_of),
    freshness_tier: resolveFreshnessTier(country.freshness_tier, manifest, now),
    rank: asNumber(country.rank, index + 1),
  };
}

function normalizeForecastSnapshot(
  raw: unknown,
  manifest: LiveSnapshotManifest,
  now: Date,
): LiveSnapshotForecastSnapshot | null {
  if (!isRecord(raw)) {
    return null;
  }

  const countries = Array.isArray(raw.countries)
    ? raw.countries.map((entry, index) => normalizeForecastCountry(entry, manifest, index, now))
    : [];

  countries.sort((left, right) => left.rank - right.rank || right.score - left.score || left.iso3.localeCompare(right.iso3));
  const leadCountry = countries[0] ?? null;

  return {
    forecast_as_of: asString(raw.forecast_as_of, manifest.forecast_as_of),
    lead_country_iso3: asNullableString(raw.lead_country_iso3 ?? leadCountry?.iso3 ?? manifest.top_country_iso3),
    lead_country_name: asNullableString(raw.lead_country_name ?? leadCountry?.country_name ?? manifest.top_country_name),
    predicted_conflict: normalizePredictedConflict(raw.predicted_conflict, {
      iso3: asNullableString(raw.lead_country_iso3 ?? leadCountry?.iso3 ?? manifest.top_country_iso3),
      country_name: asNullableString(raw.lead_country_name ?? leadCountry?.country_name ?? manifest.top_country_name),
      target_name: asString(raw.primary_target, manifest.primary_target),
      horizon_days: manifest.predicted_conflict.horizon_days,
      summary: manifest.predicted_conflict.summary,
      report_slug: manifest.predicted_conflict.report_slug,
    }),
    primary_target: asString(raw.primary_target, manifest.primary_target),
    alert_type: asString(raw.alert_type, manifest.alert_type) as LiveSnapshotForecastSnapshot["alert_type"],
    no_clear_leader: asBoolean(raw.no_clear_leader, manifest.no_clear_leader),
    coverage_count: asNumber(raw.coverage_count, countries.length),
    countries,
  };
}

function normalizeBacktestDelta(raw: unknown): LiveSnapshotBacktestDelta {
  const delta = isRecord(raw) ? raw : {};
  return {
    model_name: asString(delta.model_name, "unknown"),
    delta_pr_auc: typeof delta.delta_pr_auc === "number" ? delta.delta_pr_auc : null,
    delta_roc_auc: typeof delta.delta_roc_auc === "number" ? delta.delta_roc_auc : null,
    delta_f1: typeof delta.delta_f1 === "number" ? delta.delta_f1 : null,
    delta_brier_score: typeof delta.delta_brier_score === "number" ? delta.delta_brier_score : null,
  };
}

function synthesizeBacktestSummary(manifest: LiveSnapshotManifest, modelCard: LiveSnapshotModelCard): LiveSnapshotBacktestSummary {
  const primaryModelName =
    modelCard.model_name ||
    manifest.provenance.onset?.training.model_name ||
    manifest.provenance.escalation?.training.model_name ||
    "unknown";
  return {
    primary_model: primaryModelName,
    baseline_model: null,
    top_model_name: modelCard.model_name || null,
    primary_target: modelCard.primary_target,
    alert_type: modelCard.alert_type,
    model_status: modelCard.model_status,
    no_clear_leader: manifest.no_clear_leader,
    publish_threshold: modelCard.threshold_policy.publish_threshold,
    alert_threshold: modelCard.threshold_policy.alert_threshold,
    episode_recall: modelCard.metrics.episode_recall,
    false_alerts_per_true_alert: modelCard.metrics.false_alerts_per_true_alert,
    recall_at_5: modelCard.metrics.recall_at_5,
    recall_at_10: modelCard.metrics.recall_at_10,
    no_clear_leader_rate: modelCard.metrics.no_clear_leader_rate,
    false_alert_burden: null,
    new_alert_count: null,
    true_alert_count: null,
    false_alert_count: null,
    calibration_method: null,
    baseline_deltas: [],
    plots: null,
  };
}

function normalizeBacktestSummary(raw: unknown, manifest: LiveSnapshotManifest, modelCard: LiveSnapshotModelCard): LiveSnapshotBacktestSummary {
  if (!isRecord(raw)) {
    return synthesizeBacktestSummary(manifest, modelCard);
  }

  return {
    primary_model:
      asString(
        raw.primary_model,
        modelCard.model_name ||
          manifest.provenance.onset?.training.model_name ||
          manifest.provenance.escalation?.training.model_name ||
          "unknown",
      ),
    baseline_model: asNullableString(raw.baseline_model),
    top_model_name: asNullableString(raw.top_model_name),
    primary_target: asNullableString(raw.primary_target ?? modelCard.primary_target),
    alert_type: asNullableString(raw.alert_type ?? modelCard.alert_type) as LiveSnapshotBacktestSummary["alert_type"],
    model_status: asNullableString(raw.model_status ?? modelCard.model_status) as LiveSnapshotBacktestSummary["model_status"],
    no_clear_leader: typeof raw.no_clear_leader === "boolean" ? raw.no_clear_leader : manifest.no_clear_leader,
    publish_threshold: typeof raw.publish_threshold === "number" ? raw.publish_threshold : modelCard.threshold_policy.publish_threshold,
    alert_threshold: typeof raw.alert_threshold === "number" ? raw.alert_threshold : modelCard.threshold_policy.alert_threshold,
    episode_recall: typeof raw.episode_recall === "number" ? raw.episode_recall : modelCard.metrics.episode_recall,
    false_alerts_per_true_alert:
      typeof raw.false_alerts_per_true_alert === "number"
        ? raw.false_alerts_per_true_alert
        : modelCard.metrics.false_alerts_per_true_alert,
    recall_at_5: typeof raw.recall_at_5 === "number" ? raw.recall_at_5 : modelCard.metrics.recall_at_5,
    recall_at_10: typeof raw.recall_at_10 === "number" ? raw.recall_at_10 : modelCard.metrics.recall_at_10,
    no_clear_leader_rate:
      typeof raw.no_clear_leader_rate === "number" ? raw.no_clear_leader_rate : modelCard.metrics.no_clear_leader_rate,
    false_alert_burden: typeof raw.false_alert_burden === "number" ? raw.false_alert_burden : null,
    new_alert_count: typeof raw.new_alert_count === "number" ? raw.new_alert_count : null,
    true_alert_count: typeof raw.true_alert_count === "number" ? raw.true_alert_count : null,
    false_alert_count: typeof raw.false_alert_count === "number" ? raw.false_alert_count : null,
    calibration_method: asNullableString(raw.calibration_method),
    baseline_deltas: Array.isArray(raw.baseline_deltas) ? raw.baseline_deltas.map(normalizeBacktestDelta) : [],
    plots: isRecord(raw.plots)
      ? {
          probability_distribution: asNullableString(raw.plots.probability_distribution),
          precision_recall: asNullableString(raw.plots.precision_recall),
        }
      : null,
  };
}

function computeLeadTieCount(countries: LiveSnapshotForecastCountry[]): number {
  if (countries.length === 0) {
    return 0;
  }

  const topScore = countries[0].score;
  return countries.filter((country) => Math.abs(country.score - topScore) <= 1e-12).length;
}

function appendMessage(base: string | null, message: string | null): string | null {
  if (!message) {
    return base;
  }
  if (!base) {
    return message;
  }
  if (base.includes(message)) {
    return base;
  }
  return `${base} ${message}`;
}

function getSnapshotInputToken(pathOrFile: string): string {
  if (!fs.existsSync(pathOrFile)) {
    return "missing";
  }

  const stat = fs.statSync(pathOrFile);
  if (!stat.isDirectory()) {
    return `${stat.mtimeMs}`;
  }

  const trackedFiles = ["manifest.json", "forecast_snapshot.json", "model_card.json", "backtest_summary.json", "status.json"]
    .map((entry) => path.join(pathOrFile, entry))
    .filter((entry) => fs.existsSync(entry))
    .map((entry) => `${path.basename(entry)}:${fs.statSync(entry).mtimeMs}`);

  const countriesDir = path.join(pathOrFile, "countries");
  if (fs.existsSync(countriesDir) && fs.statSync(countriesDir).isDirectory()) {
    trackedFiles.push(`countries:${fs.statSync(countriesDir).mtimeMs}`);
  }

  return trackedFiles.length > 0 ? trackedFiles.join("|") : `${stat.mtimeMs}`;
}

function normalizeCountryDetail(
  raw: unknown,
  forecastCountry: LiveSnapshotForecastCountry,
  manifest: LiveSnapshotManifest,
  modelCard: LiveSnapshotModelCard,
  now: Date,
): LiveSnapshotCountryDetail {
  const detail = isRecord(raw) ? raw : {};
  const rawForecast = isRecord(detail.forecast) ? detail.forecast : {};

  return {
    iso3: asString(detail.iso3, forecastCountry.iso3),
    country_name: asString(detail.country_name, forecastCountry.country_name),
    region_name: asNullableString(detail.region_name ?? forecastCountry.region_name),
    report_slug: asString(detail.report_slug, `${forecastCountry.iso3.toLowerCase()}-latest`),
    summary: asString(detail.summary, `${forecastCountry.country_name} is included in the published site snapshot.`),
    chronology: asStringArray(detail.chronology).length > 0 ? asStringArray(detail.chronology) : [`Forecast as of ${forecastCountry.forecast_as_of}.`],
    top_drivers: asStringArray(detail.top_drivers),
    forecast: {
      score: asNumber(rawForecast.score, forecastCountry.score),
      delta: asNumber(rawForecast.delta, forecastCountry.delta),
      rank: asNumber(rawForecast.rank, forecastCountry.rank),
      forecast_as_of: asString(rawForecast.forecast_as_of, forecastCountry.forecast_as_of),
      freshness_tier: resolveFreshnessTier(rawForecast.freshness_tier, manifest, now),
      model_name: asString(rawForecast.model_name, modelCard.model_name),
      model_version: asString(rawForecast.model_version, modelCard.model_version),
      target_name: asString(rawForecast.target_name, modelCard.target_name),
      horizon_days: asNumber(rawForecast.horizon_days, modelCard.horizon_days),
    },
    source_snapshot_hash: asNullableString(detail.source_snapshot_hash),
  };
}

function buildCountryDetails(
  countriesDir: string,
  forecastSnapshot: LiveSnapshotForecastSnapshot,
  manifest: LiveSnapshotManifest,
  modelCard: LiveSnapshotModelCard,
  now: Date,
): Record<string, LiveSnapshotCountryDetail> {
  const details = new Map<string, LiveSnapshotCountryDetail>();

  for (const entry of readJsonDirectory<Record<string, unknown>>(countriesDir)) {
    const rawDetail = entry.value;
    const iso3 = asString(rawDetail.iso3).toUpperCase();
    const forecastCountry = forecastSnapshot.countries.find((country) => country.iso3 === iso3);
    if (!forecastCountry) {
      continue;
    }
    details.set(iso3.toLowerCase(), normalizeCountryDetail(rawDetail, forecastCountry, manifest, modelCard, now));
  }

  for (const forecastCountry of forecastSnapshot.countries) {
    const key = forecastCountry.iso3.toLowerCase();
    if (!details.has(key)) {
      details.set(key, normalizeCountryDetail(null, forecastCountry, manifest, modelCard, now));
    }
  }

  return Object.fromEntries(details.entries());
}

function normalizeStatus(
  raw: unknown,
  manifest: LiveSnapshotManifest | null,
  forecastSnapshot: LiveSnapshotForecastSnapshot | null,
  sourceKind: LiveSnapshotSourceKind,
  sourcePath: string | null,
  now: Date,
): LiveSnapshotStatus {
  const predictionFile = isRecord(raw) ? asNullableString(raw.prediction_file) : null;
  const leadTieCount =
    isRecord(raw) && typeof raw.lead_tie_count === "number"
      ? raw.lead_tie_count
      : forecastSnapshot
        ? computeLeadTieCount(forecastSnapshot.countries)
        : null;
  const baseStatus = buildLiveSnapshotStatus({
    manifest,
    source_kind: sourceKind,
    source_path: sourcePath,
    prediction_file: predictionFile,
    lead_tie_count: leadTieCount,
    message: isRecord(raw) ? asNullableString(raw.message) : null,
    now,
  });
  const manifestPrimaryTarget = manifest?.primary_target ?? forecastSnapshot?.primary_target ?? null;
  const manifestAlertType = manifest?.alert_type ?? forecastSnapshot?.alert_type ?? null;
  const manifestModelStatus = manifest?.model_status ?? null;
  const manifestNoClearLeader = manifest?.no_clear_leader ?? forecastSnapshot?.no_clear_leader ?? null;

  return {
    ...baseStatus,
    primary_target: isRecord(raw) ? asNullableString(raw.primary_target ?? manifestPrimaryTarget) : manifestPrimaryTarget,
    alert_type: (isRecord(raw) ? asNullableString(raw.alert_type ?? manifestAlertType) : manifestAlertType) as LiveSnapshotStatus["alert_type"],
    model_status: (isRecord(raw) ? asNullableString(raw.model_status ?? manifestModelStatus) : manifestModelStatus) as LiveSnapshotStatus["model_status"],
    no_clear_leader:
      isRecord(raw) && typeof raw.no_clear_leader === "boolean" ? raw.no_clear_leader : manifestNoClearLeader,
    predicted_conflict: normalizePredictedConflict(isRecord(raw) ? raw.predicted_conflict : null, {
      iso3: forecastSnapshot?.lead_country_iso3 ?? manifest?.top_country_iso3 ?? null,
      country_name: forecastSnapshot?.lead_country_name ?? manifest?.top_country_name ?? null,
      target_name: manifestPrimaryTarget ?? "escalation",
      horizon_days: forecastSnapshot?.predicted_conflict.horizon_days ?? manifest?.predicted_conflict.horizon_days ?? 30,
      summary: forecastSnapshot?.predicted_conflict.summary ?? manifest?.predicted_conflict.summary ?? null,
      report_slug: forecastSnapshot?.predicted_conflict.report_slug ?? manifest?.predicted_conflict.report_slug ?? null,
    }),
    publish_threshold:
      isRecord(raw) && typeof raw.publish_threshold === "number" ? raw.publish_threshold : null,
    alert_threshold:
      isRecord(raw) && typeof raw.alert_threshold === "number" ? raw.alert_threshold : null,
  };
}

function buildLiveSnapshotBundle({
  manifest,
  forecastSnapshot,
  modelCard,
  backtestSummary,
  status,
  countryDetails,
  sourceKind,
  sourcePath,
}: {
  manifest: LiveSnapshotManifest;
  forecastSnapshot: LiveSnapshotForecastSnapshot;
  modelCard: LiveSnapshotModelCard;
  backtestSummary: LiveSnapshotBacktestSummary;
  status: LiveSnapshotStatus;
  countryDetails: Record<string, LiveSnapshotCountryDetail>;
  sourceKind: LiveSnapshotSourceKind;
  sourcePath: string;
}): LiveSnapshotBundle {
  return {
    manifest,
    forecast_snapshot: forecastSnapshot,
    model_card: modelCard,
    backtest_summary: backtestSummary,
    status,
    country_details: countryDetails,
    source_kind: sourceKind,
    source_path: sourcePath,
  };
}

function loadPreferredBundle(bundleDir: string, now: Date): { result: LiveSnapshotLoadResult | null; error: string | null } {
  if (!fs.existsSync(bundleDir) || !fs.statSync(bundleDir).isDirectory()) {
    return { result: null, error: null };
  }

  const manifestRead = readJsonResult(path.join(bundleDir, "manifest.json"));
  if (manifestRead.error) {
    return { result: null, error: manifestRead.error };
  }
  const manifest = normalizeManifest(manifestRead.value);

  const forecastSnapshotRead = readJsonResult(path.join(bundleDir, "forecast_snapshot.json"));
  if (forecastSnapshotRead.error) {
    return { result: null, error: forecastSnapshotRead.error };
  }

  const modelCardRead = readJsonResult(path.join(bundleDir, "model_card.json"));
  if (modelCardRead.error) {
    return { result: null, error: modelCardRead.error };
  }

  const modelCard = manifest ? normalizeModelCard(modelCardRead.value, manifest) : null;

  if (!manifest || !forecastSnapshotRead.value || !modelCard) {
    return { result: null, error: "Preferred site snapshot bundle is incomplete." };
  }

  const forecastSnapshot = normalizeForecastSnapshot(forecastSnapshotRead.value, manifest, now);
  if (!forecastSnapshot) {
    return { result: null, error: "Preferred forecast_snapshot.json is invalid." };
  }

  const backtestSummaryRead = readJsonResult(path.join(bundleDir, "backtest_summary.json"));
  if (backtestSummaryRead.error) {
    return { result: null, error: backtestSummaryRead.error };
  }

  const statusRead = readJsonResult(path.join(bundleDir, "status.json"));
  if (statusRead.error) {
    return { result: null, error: statusRead.error };
  }

  const backtestSummary = normalizeBacktestSummary(backtestSummaryRead.value, manifest, modelCard);
  const status = normalizeStatus(
    statusRead.value,
    manifest,
    forecastSnapshot,
    "preferred",
    bundleDir,
    now,
  );
  const countryDetails = buildCountryDetails(path.join(bundleDir, "countries"), forecastSnapshot, manifest, modelCard, now);

  const bundle = buildLiveSnapshotBundle({
    manifest,
    forecastSnapshot,
    modelCard,
    backtestSummary,
    status,
    countryDetails,
    sourceKind: "preferred",
    sourcePath: bundleDir,
  });

  return {
    result: {
      bundle,
      status,
      source_kind: "preferred",
      source_path: bundleDir,
    },
    error: null,
  };
}

function loadFallbackBundle(bundleFile: string, now: Date): { result: LiveSnapshotLoadResult | null; error: string | null } {
  if (!fs.existsSync(bundleFile) || !fs.statSync(bundleFile).isFile()) {
    return { result: null, error: null };
  }

  const rawRead = readJsonResult(bundleFile);
  if (rawRead.error) {
    return { result: null, error: rawRead.error };
  }

  const raw = rawRead.value;
  if (!isRecord(raw)) {
    return { result: null, error: "Fallback snapshot bundle is invalid." };
  }

  const manifest = normalizeManifest(raw.manifest);
  const forecastSnapshotRaw = raw.forecast_snapshot;
  const modelCard = manifest ? normalizeModelCard(raw.model_card, manifest) : null;

  if (!manifest || !forecastSnapshotRaw || !modelCard) {
    return { result: null, error: "Fallback snapshot bundle is incomplete." };
  }

  const forecastSnapshot = normalizeForecastSnapshot(forecastSnapshotRaw, manifest, now);
  if (!forecastSnapshot) {
    return { result: null, error: "Fallback forecast snapshot is invalid." };
  }

  const backtestSummary = normalizeBacktestSummary(raw.backtest_summary, manifest, modelCard);
  const status = normalizeStatus(raw.status, manifest, forecastSnapshot, "fallback", bundleFile, now);
  const countryDetails = buildCountryDetails(path.dirname(bundleFile), forecastSnapshot, manifest, modelCard, now);

  const bundle = buildLiveSnapshotBundle({
    manifest,
    forecastSnapshot,
    modelCard,
    backtestSummary,
    status,
    countryDetails,
    sourceKind: "fallback",
    sourcePath: bundleFile,
  });

  return {
    result: {
      bundle,
      status,
      source_kind: "fallback",
      source_path: bundleFile,
    },
    error: null,
  };
}

function makeCacheKey({
  preferredBundleDir = defaultPreferredBundleDir,
  fallbackBundleFile = defaultFallbackBundleFile,
}: {
  preferredBundleDir?: string;
  fallbackBundleFile?: string;
  now?: Date;
}): string {
  return [
    preferredBundleDir,
    getSnapshotInputToken(preferredBundleDir),
    fallbackBundleFile,
    getSnapshotInputToken(fallbackBundleFile),
  ].join("::");
}

export function clearLiveSnapshotCache(): void {
  liveSnapshotCache.clear();
}

export function loadLiveSnapshot({
  preferredBundleDir = defaultPreferredBundleDir,
  fallbackBundleFile = defaultFallbackBundleFile,
  now = new Date(),
}: {
  preferredBundleDir?: string;
  fallbackBundleFile?: string;
  now?: Date;
} = {}): LiveSnapshotLoadResult {
  const preferred = loadPreferredBundle(preferredBundleDir, now);
  if (preferred.result) {
    return preferred.result;
  }

  const fallback = loadFallbackBundle(fallbackBundleFile, now);
  if (fallback.result) {
    if (preferred.error) {
      fallback.result.status.message = appendMessage(fallback.result.status.message, preferred.error);
      if (fallback.result.bundle) {
        fallback.result.bundle.status.message = fallback.result.status.message;
      }
    }
    return fallback.result;
  }

  const status = buildLiveSnapshotStatus({
    manifest: null,
    source_kind: "missing",
    source_path: null,
    prediction_file: null,
    lead_tie_count: null,
    message: appendMessage(preferred.error, fallback.error),
    now,
  });

  return {
    bundle: null,
    status,
    source_kind: "missing",
    source_path: null,
  };
}

export function getLiveSnapshot(options: {
  preferredBundleDir?: string;
  fallbackBundleFile?: string;
  now?: Date;
} = {}): LiveSnapshotLoadResult {
  const cacheKey = makeCacheKey(options);
  const cached = liveSnapshotCache.get(cacheKey);
  if (cached) {
    return cached;
  }

  const result = loadLiveSnapshot(options);
  liveSnapshotCache.set(cacheKey, result);
  return result;
}
