import assert from "node:assert/strict";
import test from "node:test";

import {
  buildOperationalCountriesFromSnapshot,
  buildOperationalStatusSummaryFromSnapshot,
  getLeadCountry,
  getOperationalCountries,
  getOperationalCountryBySlug,
  getOperationalForecastRows,
  getOperationalStatusSummary,
} from "@/lib/site-data-core";

test("maps the published snapshot into operational country records", () => {
  const countries = getOperationalCountries();

  assert.equal(countries.length, 30);
  assert.equal(countries[0]?.iso3, "AUS");
  assert.equal(countries[0]?.slug, "australia");
  assert.equal(countries[0]?.shapeKey, null);

  const iran = countries.find((country) => country.iso3 === "IRN");
  assert.ok(iran);
  assert.equal(iran?.slug, "iran");
  assert.equal(iran?.shapeKey, "iran");
  assert.equal(iran?.dossierAvailable, true);
});

test("exposes the published lead country as an arbitrary-country route", () => {
  const leadCountry = getLeadCountry();
  const australia = getOperationalCountryBySlug("australia");

  assert.ok(leadCountry);
  assert.equal(leadCountry?.iso3, "AUS");
  assert.ok(australia);
  assert.equal(australia?.iso3, "AUS");
  assert.equal(australia?.dossierAvailable, false);
});

test("builds operational forecast rows and status from the canonical snapshot bundle", () => {
  const rows = getOperationalForecastRows();
  const status = getOperationalStatusSummary();

  assert.equal(rows.length, 30);
  assert.equal(rows[0]?.iso3, "AUS");
  assert.equal(status.sourceKind, "preferred");
  assert.equal(status.coverageCount, 30);
  assert.equal(status.leadCountryIso3, "AUS");
  assert.equal(status.leadTieCount, 16);
  assert.equal(status.modelName, "logit");
  assert.equal(status.topModelName, "prior_rate");
});

test("maps onset-first alert semantics and abstention from the published snapshot bundle", () => {
  const snapshot = {
    source_kind: "preferred",
    source_path: "/tmp/site-snapshot",
    status: {
      status: "ok",
      freshness_tier: "fresh",
      published_at: "2026-03-28T12:00:00Z",
      forecast_as_of: "2026-03-23",
      baseline_used: false,
      coverage_count: 2,
      lead_country_iso3: "LBN",
      lead_country_name: "Lebanon",
      prediction_file: "/tmp/site-snapshot/predictions.parquet",
      lead_tie_count: 2,
      primary_target: "onset",
      alert_type: "No Clear Leader",
      model_status: "monitoring_only",
      no_clear_leader: true,
      publish_threshold: 0.82,
      alert_threshold: 0.76,
      source_kind: "preferred",
      source_path: "/tmp/site-snapshot",
      message: "Lead ranking is currently weak.",
    },
    bundle: {
      manifest: {
        schema_version: "1.0.0",
        snapshot_id: "site_snapshot-2026-03-28",
        published_at: "2026-03-28T12:00:00Z",
        fresh_until: "2026-04-07T12:00:00Z",
        stale_after: "2026-04-18T12:00:00Z",
        baseline_used: false,
        forecast_as_of: "2026-03-23",
        generated_at: "2026-03-28T12:00:00Z",
        coverage_count: 2,
        top_country_iso3: "LBN",
        top_country_name: "Lebanon",
        primary_target: "onset",
        alert_type: "No Clear Leader",
        model_status: "monitoring_only",
        no_clear_leader: true,
        provenance: {
          onset: {
            training: { run_name: "train_country_week_onset_logit_30d", artifact_path: "a", completed_at: "2026-03-28T10:00:00Z", model_name: "logit" },
            calibration: { run_name: "country_week_onset_logit", artifact_path: "b", completed_at: "2026-03-28T10:30:00Z", model_name: "logit" },
            backtest: { run_name: "country_week_onset_logit", artifact_path: "c", completed_at: "2026-03-28T11:00:00Z", model_name: "logit" },
          },
          escalation: {
            training: { run_name: "train_country_week_logit_30d", artifact_path: "d", completed_at: "2026-03-28T10:00:00Z", model_name: "logit" },
            calibration: { run_name: "country_week_logit", artifact_path: "e", completed_at: "2026-03-28T10:30:00Z", model_name: "logit" },
            backtest: { run_name: "country_week_logit", artifact_path: "f", completed_at: "2026-03-28T11:00:00Z", model_name: "logit" },
          },
          structural: {
            training: { run_name: "train_country_week_onset_structural_90d", artifact_path: "g", completed_at: "2026-03-28T09:45:00Z", model_name: "logit" },
            calibration: { run_name: "country_week_onset_structural_90d", artifact_path: "h", completed_at: "2026-03-28T10:00:00Z", model_name: "logit" },
            backtest: { run_name: "country_week_onset_structural_90d", artifact_path: "i", completed_at: "2026-03-28T10:15:00Z", model_name: "logit" },
          },
        },
      },
      forecast_snapshot: {
        forecast_as_of: "2026-03-23",
        lead_country_iso3: "LBN",
        lead_country_name: "Lebanon",
        primary_target: "onset",
        alert_type: "No Clear Leader",
        no_clear_leader: true,
        coverage_count: 2,
        countries: [
          { iso3: "LBN", country_name: "Lebanon", region_name: "Middle East", score: 0.41, delta: 0.02, forecast_as_of: "2026-03-23", freshness_tier: "fresh", rank: 1 },
          { iso3: "ISR", country_name: "Israel", region_name: "Middle East", score: 0.405, delta: 0.01, forecast_as_of: "2026-03-23", freshness_tier: "fresh", rank: 2 },
        ],
      },
      model_card: {
        model_name: "logit",
        model_version: "country_week_onset_logit_30d",
        target_name: "country_week_onset_30d",
        horizon_days: 30,
        published_at: "2026-03-28T12:00:00Z",
        stale_after: "2026-04-18T12:00:00Z",
        baseline_used: false,
        primary_target: "onset",
        alert_type: "No Clear Leader",
        model_status: "monitoring_only",
        metrics: {
          brier_score: 0.14,
          roc_auc: 0.81,
          precision_at_10: 0.3,
          recall_at_5: 0.31,
          recall_at_10: 0.52,
          episode_recall: 0.44,
          false_alerts_per_true_alert: 1,
          no_clear_leader_rate: 0.14,
        },
        threshold_policy: {
          publish_top_n: 10,
          publish_threshold: 0.82,
          alert_threshold: 0.76,
          warning_threshold: 0.5,
          operating_threshold: 0.6,
        },
        provenance: {
          onset: {
            training: { run_name: "train_country_week_onset_logit_30d", artifact_path: "a", completed_at: "2026-03-28T10:00:00Z", model_name: "logit" },
            calibration: { run_name: "country_week_onset_logit", artifact_path: "b", completed_at: "2026-03-28T10:30:00Z", model_name: "logit" },
            backtest: { run_name: "country_week_onset_logit", artifact_path: "c", completed_at: "2026-03-28T11:00:00Z", model_name: "logit" },
          },
          escalation: {
            training: { run_name: "train_country_week_logit_30d", artifact_path: "d", completed_at: "2026-03-28T10:00:00Z", model_name: "logit" },
            calibration: { run_name: "country_week_logit", artifact_path: "e", completed_at: "2026-03-28T10:30:00Z", model_name: "logit" },
            backtest: { run_name: "country_week_logit", artifact_path: "f", completed_at: "2026-03-28T11:00:00Z", model_name: "logit" },
          },
          structural: {
            training: { run_name: "train_country_week_onset_structural_90d", artifact_path: "g", completed_at: "2026-03-28T09:45:00Z", model_name: "logit" },
            calibration: { run_name: "country_week_onset_structural_90d", artifact_path: "h", completed_at: "2026-03-28T10:00:00Z", model_name: "logit" },
            backtest: { run_name: "country_week_onset_structural_90d", artifact_path: "i", completed_at: "2026-03-28T10:15:00Z", model_name: "logit" },
          },
        },
      },
      backtest_summary: {
        primary_model: "logit",
        baseline_model: "prior_rate",
        top_model_name: "prior_rate",
        primary_target: "onset",
        alert_type: "No Clear Leader",
        model_status: "monitoring_only",
        no_clear_leader: true,
        publish_threshold: 0.82,
        alert_threshold: 0.76,
        episode_recall: 0.44,
        false_alerts_per_true_alert: 1,
        recall_at_5: 0.31,
        recall_at_10: 0.52,
        no_clear_leader_rate: 0.14,
        false_alert_burden: 1,
        new_alert_count: 2,
        true_alert_count: 1,
        false_alert_count: 1,
        calibration_method: "isotonic",
        baseline_deltas: [],
        plots: null,
      },
      country_details: {
        lbn: {
          iso3: "LBN",
          country_name: "Lebanon",
          region_name: "Middle East",
          report_slug: "lbn-latest",
          summary: "Lead ranking is weak even though Lebanon remains near the top.",
          chronology: ["Week of 2026-03-23: alert separation remained thin."],
          top_drivers: ["Recent event acceleration"],
          forecast: {
            score: 0.41,
            delta: 0.02,
            rank: 1,
            forecast_as_of: "2026-03-23",
            freshness_tier: "fresh",
            model_name: "logit",
            model_version: "country_week_onset_logit_30d",
            target_name: "country_week_onset_30d",
            horizon_days: 30,
          },
          source_snapshot_hash: "hash-lbn",
        },
      },
      source_kind: "preferred",
      source_path: "/tmp/site-snapshot",
      status: null,
    },
  } as const;

  const status = buildOperationalStatusSummaryFromSnapshot(snapshot);
  const countries = buildOperationalCountriesFromSnapshot(snapshot);

  assert.equal(status.primaryTarget, "onset");
  assert.equal(status.alertType, "No Clear Leader");
  assert.equal(status.modelStatus, "monitoring_only");
  assert.equal(status.noClearLeader, true);
  assert.equal(status.publishThreshold, 0.82);
  assert.equal(status.recallAt10, 0.52);
  assert.equal(status.episodeRecall, 0.44);
  assert.equal(status.structuralPriorActive, true);
  assert.equal(status.structuralPriorRunName, "train_country_week_onset_structural_90d");
  assert.equal(status.structuralPriorModelName, "logit");
  assert.equal(status.structuralPriorCompletedAt, "2026-03-28T10:15:00.000Z");
  assert.equal(countries[0]?.iso3, "LBN");
  assert.equal(countries[0]?.targetName, "country_week_onset_30d");
});
