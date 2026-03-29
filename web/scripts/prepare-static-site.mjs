import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const webDir = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(webDir, "..");

const preferredBundleDir = path.join(repoRoot, "artifacts", "website_publishing", "site_snapshot", "latest");
const fallbackBundleFile = path.join(repoRoot, "artifacts", "examples", "website_snapshot_example.json");
const publicDir = path.join(webDir, "public");
const publicBundleDir = path.join(publicDir, "site-snapshot", "latest");
const publicApiDir = path.join(publicDir, "api");

async function exists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

async function ensureDir(dirPath) {
  await fs.mkdir(dirPath, { recursive: true });
}

function buildFallbackStatus(bundle) {
  return {
    status: "fallback",
    freshness_tier: "fresh",
    published_at: bundle.manifest.published_at,
    forecast_as_of: bundle.manifest.forecast_as_of,
    baseline_used: bundle.manifest.baseline_used,
    coverage_count: bundle.forecast_snapshot.coverage_count,
    predicted_conflict: bundle.forecast_snapshot.predicted_conflict,
    primary_target: bundle.forecast_snapshot.primary_target,
    alert_type: bundle.forecast_snapshot.alert_type,
    model_status: bundle.model_card.model_status,
    no_clear_leader: bundle.forecast_snapshot.no_clear_leader,
    publish_threshold: bundle.model_card.threshold_policy.publish_threshold ?? null,
    alert_threshold: bundle.model_card.threshold_policy.alert_threshold ?? null,
    lead_country_iso3: bundle.forecast_snapshot.lead_country_iso3,
    lead_country_name: bundle.forecast_snapshot.lead_country_name,
    prediction_file: null,
    lead_tie_count: null,
    message: "Preferred site snapshot unavailable; using bundled fallback snapshot.",
  };
}

function buildHealthPayload({ manifest, status }) {
  const structural = manifest?.provenance?.structural ?? null;
  return {
    ok: status.status !== "missing",
    status,
    structural_prior: {
      present: Boolean(structural),
      run_name: structural?.training?.run_name ?? null,
      model_name: structural?.training?.model_name ?? null,
      completed_at: structural?.training?.completed_at ?? null,
    },
  };
}

async function copyPreferredBundle() {
  await fs.rm(publicBundleDir, { recursive: true, force: true });
  await ensureDir(path.dirname(publicBundleDir));
  await fs.cp(preferredBundleDir, publicBundleDir, { recursive: true });

  const manifest = await readJson(path.join(publicBundleDir, "manifest.json"));
  const status = await readJson(path.join(publicBundleDir, "status.json"));
  return { manifest, status };
}

async function writeFallbackBundle() {
  const bundle = await readJson(fallbackBundleFile);
  const status = buildFallbackStatus(bundle);

  await fs.rm(publicBundleDir, { recursive: true, force: true });
  await ensureDir(publicBundleDir);
  await fs.writeFile(path.join(publicBundleDir, "manifest.json"), JSON.stringify(bundle.manifest, null, 2));
  await fs.writeFile(path.join(publicBundleDir, "forecast_snapshot.json"), JSON.stringify(bundle.forecast_snapshot, null, 2));
  await fs.writeFile(path.join(publicBundleDir, "model_card.json"), JSON.stringify(bundle.model_card, null, 2));
  await fs.writeFile(
    path.join(publicBundleDir, "backtest_summary.json"),
    JSON.stringify(
      {
        primary_model: bundle.model_card.model_name,
        baseline_model: null,
        top_model_name: bundle.model_card.model_name,
        primary_target: bundle.forecast_snapshot.primary_target,
        alert_type: bundle.forecast_snapshot.alert_type,
        model_status: bundle.model_card.model_status,
        no_clear_leader: bundle.forecast_snapshot.no_clear_leader,
        publish_threshold: bundle.model_card.threshold_policy.publish_threshold ?? null,
        alert_threshold: bundle.model_card.threshold_policy.alert_threshold ?? null,
        episode_recall: bundle.model_card.metrics.episode_recall ?? null,
        false_alerts_per_true_alert: bundle.model_card.metrics.false_alerts_per_true_alert ?? null,
        recall_at_5: bundle.model_card.metrics.recall_at_5 ?? null,
        recall_at_10: bundle.model_card.metrics.recall_at_10 ?? null,
        no_clear_leader_rate: bundle.model_card.metrics.no_clear_leader_rate ?? null,
        false_alert_burden: null,
        new_alert_count: null,
        true_alert_count: null,
        false_alert_count: null,
        calibration_method: null,
        baseline_deltas: [],
      },
      null,
      2,
    ),
  );
  await fs.writeFile(path.join(publicBundleDir, "status.json"), JSON.stringify(status, null, 2));
  await ensureDir(path.join(publicBundleDir, "countries"));

  return { manifest: bundle.manifest, status };
}

async function main() {
  await ensureDir(publicDir);
  await ensureDir(publicApiDir);

  const hasPreferredBundle =
    (await exists(preferredBundleDir)) &&
    (await exists(path.join(preferredBundleDir, "manifest.json"))) &&
    (await exists(path.join(preferredBundleDir, "forecast_snapshot.json"))) &&
    (await exists(path.join(preferredBundleDir, "model_card.json")));

  const bundleState = hasPreferredBundle ? await copyPreferredBundle() : await writeFallbackBundle();
  const health = buildHealthPayload(bundleState);

  await fs.writeFile(path.join(publicApiDir, "health.json"), JSON.stringify(health, null, 2));
  await fs.writeFile(path.join(publicApiDir, "status.json"), JSON.stringify(bundleState.status, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
