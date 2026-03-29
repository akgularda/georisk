import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { clearLiveSnapshotCache, getLiveSnapshot, loadLiveSnapshot } from "@/lib/live-snapshot";
import { getFreshnessTierForAge, getFreshnessTierFromPublishedAt } from "@/lib/freshness";
import { buildLiveSnapshotStatus } from "@/lib/status";

const repoRoot = path.resolve(process.cwd(), "..");
const fallbackBundleFile = path.join(repoRoot, "artifacts", "examples", "website_snapshot_example.json");
const preferredBundleDir = path.join(repoRoot, "artifacts", "website_publishing", "site_snapshot", "latest");

test("loads the canonical preferred bundle from the published site snapshot", () => {
  clearLiveSnapshotCache();
  const result = loadLiveSnapshot({ now: new Date("2026-03-28T12:00:00Z") });

  assert.equal(result.source_kind, "preferred");
  assert.ok(result.bundle);
  assert.match(result.bundle?.manifest.snapshot_id ?? "", /^site_snapshot-2026-03-\d{2}$/);
  assert.equal(result.bundle?.forecast_snapshot.lead_country_iso3, "AUS");
  assert.equal(result.bundle?.status.freshness_tier, "fresh");
  assert.equal(result.bundle?.backtest_summary.primary_model, "logit");
  assert.equal(result.bundle?.country_details["aus"]?.forecast.rank, 1);
});

test("parses structural provenance when it is present in a bundle", () => {
  clearLiveSnapshotCache();
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "live-snapshot-structural-"));
  const tempBundleDir = path.join(tempRoot, "bundle");
  fs.cpSync(preferredBundleDir, tempBundleDir, { recursive: true });

  const manifestPath = path.join(tempBundleDir, "manifest.json");
  const modelCardPath = path.join(tempBundleDir, "model_card.json");
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8")) as Record<string, unknown>;
  const modelCard = JSON.parse(fs.readFileSync(modelCardPath, "utf8")) as Record<string, unknown>;
  const structural = {
    training: {
      run_name: "train_country_week_onset_structural_90d",
      artifact_path: "artifacts/forecasting/train/country_week_onset_structural_90d",
      completed_at: "2026-03-28T09:45:00Z",
      model_name: "logit",
    },
    calibration: {
      run_name: "country_week_onset_structural_90d",
      artifact_path: "artifacts/forecasting/calibration/country_week_onset_structural_90d",
      completed_at: "2026-03-28T10:00:00Z",
      model_name: "logit",
    },
    backtest: {
      run_name: "country_week_onset_structural_90d",
      artifact_path: "artifacts/backtesting/run/country_week_onset_structural_90d",
      completed_at: "2026-03-28T10:15:00Z",
      model_name: "logit",
    },
  };

  ((manifest.provenance as Record<string, unknown>).structural as unknown) = structural;
  ((modelCard.provenance as Record<string, unknown>).structural as unknown) = structural;

  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf8");
  fs.writeFileSync(modelCardPath, JSON.stringify(modelCard, null, 2), "utf8");

  const result = loadLiveSnapshot({
    preferredBundleDir: tempBundleDir,
    fallbackBundleFile,
    now: new Date("2026-03-28T12:00:00Z"),
  });

  assert.equal(result.bundle?.manifest.provenance.structural?.training.run_name, "train_country_week_onset_structural_90d");
  assert.equal(result.bundle?.model_card.provenance.structural?.backtest.run_name, "country_week_onset_structural_90d");
});

test("falls back to the example snapshot when the preferred bundle is unavailable", () => {
  clearLiveSnapshotCache();
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "live-snapshot-fallback-"));
  const missingPreferred = path.join(tempRoot, "missing-site-snapshot");
  const result = loadLiveSnapshot({
    preferredBundleDir: missingPreferred,
    fallbackBundleFile,
    now: new Date("2026-03-28T12:00:00Z"),
  });

  assert.equal(result.source_kind, "fallback");
  assert.ok(result.bundle);
  assert.equal(result.bundle?.forecast_snapshot.lead_country_iso3, "LBN");
  assert.equal(result.bundle?.forecast_snapshot.predicted_conflict.label, "Lebanon / Israel");
  assert.equal(result.status.predicted_conflict?.reason_source, "report_inputs");
  assert.equal(result.bundle?.status.freshness_tier, "fresh");
  assert.equal(result.bundle?.backtest_summary.primary_model, "logit");
  assert.equal(result.bundle?.country_details["lbn"]?.forecast.rank, 1);
});

test("returns an explicit missing snapshot when neither source exists", () => {
  clearLiveSnapshotCache();
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "live-snapshot-missing-"));
  const result = loadLiveSnapshot({
    preferredBundleDir: path.join(tempRoot, "missing-preferred"),
    fallbackBundleFile: path.join(tempRoot, "missing-example.json"),
    now: new Date("2026-03-28T12:00:00Z"),
  });

  assert.equal(result.source_kind, "missing");
  assert.equal(result.bundle, null);
  assert.equal(result.status.freshness_tier, "missing");
  assert.equal(result.status.status, "missing");
});

test("maps freshness age buckets to the expected explicit tiers", () => {
  const publishedAt = new Date("2026-03-28T12:00:00Z");
  assert.equal(getFreshnessTierForAge(0), "fresh");
  assert.equal(getFreshnessTierForAge(10), "fresh");
  assert.equal(getFreshnessTierForAge(11), "aging");
  assert.equal(getFreshnessTierForAge(21), "aging");
  assert.equal(getFreshnessTierForAge(22), "stale");
  assert.equal(getFreshnessTierForAge(60), "stale");
  assert.equal(getFreshnessTierForAge(61), "critical");
  assert.equal(getFreshnessTierFromPublishedAt(publishedAt.toISOString(), new Date("2026-03-28T12:00:00Z")), "fresh");
});

test("builds a missing status when no manifest is available", () => {
  const status = buildLiveSnapshotStatus({
    manifest: null,
    source_kind: "missing",
    source_path: null,
    prediction_file: null,
  });

  assert.equal(status.status, "missing");
  assert.equal(status.freshness_tier, "missing");
  assert.equal(status.lead_country_iso3, null);
});

test("reuses the cached live snapshot for repeated reads", () => {
  clearLiveSnapshotCache();
  const first = getLiveSnapshot({ now: new Date("2026-03-28T12:00:00Z") });
  const second = getLiveSnapshot({ now: new Date("2026-03-28T12:00:00Z") });

  assert.equal(first, second);
});

test("invalidates the cached snapshot when the published bundle changes on the same day", () => {
  clearLiveSnapshotCache();
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "live-snapshot-cache-"));
  const tempBundleDir = path.join(tempRoot, "bundle");
  fs.cpSync(preferredBundleDir, tempBundleDir, { recursive: true });

  const first = getLiveSnapshot({
    preferredBundleDir: tempBundleDir,
    fallbackBundleFile,
    now: new Date("2026-03-28T12:00:00Z"),
  });
  const originalSnapshotId = first.bundle?.manifest.snapshot_id ?? "";
  assert.match(originalSnapshotId, /^site_snapshot-2026-03-\d{2}$/);

  const manifestPath = path.join(tempBundleDir, "manifest.json");
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8")) as { snapshot_id: string };
  manifest.snapshot_id = originalSnapshotId;
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf8");

  const second = getLiveSnapshot({
    preferredBundleDir: tempBundleDir,
    fallbackBundleFile,
    now: new Date("2026-03-28T12:00:00Z"),
  });

  assert.notEqual(first, second);
  assert.equal(second.bundle?.manifest.snapshot_id, originalSnapshotId);
});

test("surfaces a preferred bundle parse error when falling back to the bundled example snapshot", () => {
  clearLiveSnapshotCache();
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "live-snapshot-parse-"));
  const tempBundleDir = path.join(tempRoot, "bundle");
  fs.cpSync(preferredBundleDir, tempBundleDir, { recursive: true });
  fs.writeFileSync(path.join(tempBundleDir, "manifest.json"), "{bad json", "utf8");

  const result = loadLiveSnapshot({
    preferredBundleDir: tempBundleDir,
    fallbackBundleFile,
    now: new Date("2026-03-28T12:00:00Z"),
  });

  assert.equal(result.source_kind, "fallback");
  assert.match(result.status.message ?? "", /Failed to parse manifest\.json/);
});
