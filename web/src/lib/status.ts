import type { LiveSnapshotManifest, LiveSnapshotSourceKind, LiveSnapshotStatus } from "@/lib/types";
import { getFreshnessTierFromSnapshotBounds } from "@/lib/freshness";

export interface BuildLiveSnapshotStatusInput {
  manifest: LiveSnapshotManifest | null;
  source_kind: LiveSnapshotSourceKind;
  source_path: string | null;
  prediction_file?: string | null;
  lead_tie_count?: number | null;
  message?: string | null;
  now?: Date;
}

export function buildLiveSnapshotStatus({
  manifest,
  source_kind,
  source_path,
  prediction_file = null,
  lead_tie_count = null,
  message = null,
  now = new Date(),
}: BuildLiveSnapshotStatusInput): LiveSnapshotStatus {
  if (!manifest) {
    return {
      status: "missing",
      freshness_tier: "missing",
      published_at: null,
      forecast_as_of: null,
      baseline_used: null,
      coverage_count: null,
      lead_country_iso3: null,
      lead_country_name: null,
      primary_target: null,
      alert_type: null,
      model_status: null,
      no_clear_leader: null,
      predicted_conflict: null,
      publish_threshold: null,
      alert_threshold: null,
      prediction_file,
      lead_tie_count,
      source_kind,
      source_path,
      message: message ?? "Canonical website snapshot bundle is unavailable.",
    };
  }

  const freshness_tier = getFreshnessTierFromSnapshotBounds({
    publishedAt: manifest.published_at,
    freshUntil: manifest.fresh_until,
    staleAfter: manifest.stale_after,
    now,
  });

  return {
    status: source_kind === "preferred" ? "ok" : "fallback",
    freshness_tier,
    published_at: manifest.published_at,
    forecast_as_of: manifest.forecast_as_of,
    baseline_used: manifest.baseline_used,
    coverage_count: manifest.coverage_count,
    lead_country_iso3: manifest.top_country_iso3,
    lead_country_name: manifest.top_country_name,
    primary_target: manifest.primary_target,
    alert_type: manifest.alert_type,
    model_status: manifest.model_status,
    no_clear_leader: manifest.no_clear_leader,
    predicted_conflict: manifest.predicted_conflict,
    publish_threshold: null,
    alert_threshold: null,
    prediction_file,
    lead_tie_count,
    source_kind,
    source_path,
    message:
      message ??
      (source_kind === "fallback" ? "Preferred site snapshot unavailable; using bundled fallback snapshot." : null),
  };
}
