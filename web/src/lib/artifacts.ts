import path from "node:path";

import { getLiveSnapshot } from "@/lib/live-snapshot";
import type { LiveSnapshotLoadResult } from "@/lib/types";

export interface ArtifactForecastSnapshot {
  iso3: string;
  countryName: string;
  regionName: string;
  forecastDate: string;
  probability: number;
  score: number;
  delta: number;
  modelName: string;
  modelVersion: string;
  calibrationRunName: string;
  calibrationModelName: string;
  calibrationTrainingRunName: string;
  drivers: string[];
  trend: Array<{ label: string; score: number }>;
  sourcePath: string;
}

export interface ArtifactBacktestSummary {
  primaryModel: string;
  baselineModel: string | null;
  topModelName: string | null;
  falseAlertBurden: number | null;
  meanLeadDays: number | null;
  medianLeadDays: number | null;
  comparisonDeltas: Array<{
    modelName: string;
    deltaPrAuc: number | null;
    deltaRocAuc: number | null;
    deltaF1: number | null;
    deltaBrierScore: number | null;
  }>;
  plotPaths: {
    probabilityDistribution: string | null;
    precisionRecall: string | null;
  };
  sourcePath: string;
}

export interface ArtifactLoadStatus {
  forecastError: string | null;
  backtestError: string | null;
}

let forecastCache: ArtifactForecastSnapshot[] | null | undefined;
let backtestCache: ArtifactBacktestSummary | null | undefined;
let forecastErrorCache: string | null = null;
let backtestErrorCache: string | null = null;
let snapshotToken: LiveSnapshotLoadResult | null = null;

function resetIfSnapshotChanged(): void {
  const currentToken = getLiveSnapshot();
  if (snapshotToken !== currentToken) {
    snapshotToken = currentToken;
    forecastCache = undefined;
    backtestCache = undefined;
    forecastErrorCache = null;
    backtestErrorCache = null;
  }
}

function formatFallbackMessage(prefix: string): string {
  return `${prefix} Preferred site snapshot unavailable; bundled fallback snapshot is active.`;
}

export function getArtifactForecastSnapshots(): ArtifactForecastSnapshot[] | null {
  resetIfSnapshotChanged();
  if (forecastCache !== undefined) {
    return forecastCache;
  }

  const snapshot = snapshotToken ?? getLiveSnapshot();
  const bundle = snapshot.bundle;
  if (!bundle) {
    forecastErrorCache = snapshot.status.message ?? "Canonical website snapshot bundle is unavailable.";
    forecastCache = null;
    return forecastCache;
  }

  const countries = [...bundle.forecast_snapshot.countries].sort(
    (left, right) => left.rank - right.rank || right.score - left.score || left.iso3.localeCompare(right.iso3),
  );

  forecastCache = countries.map((country) => {
    const detail = bundle.country_details[country.iso3.toLowerCase()];
    const sourcePath = bundle.source_kind === "preferred" ? path.join(bundle.source_path, "forecast_snapshot.json") : bundle.source_path;
    const activeProvenance =
      bundle.manifest.primary_target === "onset" ? bundle.manifest.provenance.onset : bundle.manifest.provenance.escalation;
    return {
      iso3: country.iso3,
      countryName: detail?.country_name ?? country.country_name,
      regionName: detail?.region_name ?? country.region_name ?? "",
      forecastDate: country.forecast_as_of,
      probability: country.score,
      score: Math.round(country.score * 100),
      delta: Math.round(country.delta * 100),
      modelName: bundle.model_card.model_name,
      modelVersion: bundle.model_card.model_version,
      calibrationRunName: activeProvenance?.calibration.run_name ?? "",
      calibrationModelName: activeProvenance?.calibration.model_name ?? "",
      calibrationTrainingRunName: activeProvenance?.training.run_name ?? "",
      drivers: detail?.top_drivers ?? [],
      trend: [],
      sourcePath,
    };
  });

  if (bundle.source_kind !== "preferred") {
    forecastErrorCache = formatFallbackMessage("Forecast loader fallback active.");
  }

  return forecastCache;
}

export function getArtifactBacktestSummary(): ArtifactBacktestSummary | null {
  resetIfSnapshotChanged();
  if (backtestCache !== undefined) {
    return backtestCache;
  }

  const snapshot = snapshotToken ?? getLiveSnapshot();
  const bundle = snapshot.bundle;
  if (!bundle) {
    backtestErrorCache = snapshot.status.message ?? "Canonical website snapshot bundle is unavailable.";
    backtestCache = null;
    return backtestCache;
  }

  backtestCache = {
    primaryModel: bundle.backtest_summary.primary_model,
    baselineModel: bundle.backtest_summary.baseline_model,
    topModelName: bundle.backtest_summary.top_model_name,
    falseAlertBurden: bundle.backtest_summary.false_alert_burden,
    meanLeadDays: null,
    medianLeadDays: null,
    comparisonDeltas: bundle.backtest_summary.baseline_deltas.map((item) => ({
      modelName: item.model_name,
      deltaPrAuc: item.delta_pr_auc,
      deltaRocAuc: item.delta_roc_auc,
      deltaF1: item.delta_f1,
      deltaBrierScore: item.delta_brier_score,
    })),
    plotPaths: {
      probabilityDistribution: bundle.backtest_summary.plots?.probability_distribution ?? null,
      precisionRecall: bundle.backtest_summary.plots?.precision_recall ?? null,
    },
    sourcePath: bundle.source_kind === "preferred" ? path.join(bundle.source_path, "backtest_summary.json") : bundle.source_path,
  };

  if (bundle.source_kind !== "preferred") {
    backtestErrorCache = formatFallbackMessage("Backtest loader fallback active.");
  }

  return backtestCache;
}

export function getArtifactLoadStatus(): ArtifactLoadStatus {
  resetIfSnapshotChanged();
  if (forecastCache === undefined) {
    getArtifactForecastSnapshots();
  }
  if (backtestCache === undefined) {
    getArtifactBacktestSummary();
  }
  return {
    forecastError: forecastErrorCache,
    backtestError: backtestErrorCache,
  };
}
