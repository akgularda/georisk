# Final Output Release Plan Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Take the current onset-first GeoRisk stack from "working and honest" to a final release candidate with complete structural-prior provenance, hardened trust surfaces, aligned downstream artifacts, and a full verification pass.

**Architecture:** Keep the current two-layer approach: a slower 90-day structural onset prior and a faster 30-day onset trigger model that consumes that prior. Finish the missing edges around backtesting, publishing, web semantics, downstream report/social contracts, operational health reporting, and final release documentation so the website and artifacts tell the same story.

**Tech Stack:** Python, pandas, scikit-learn, parquet artifacts, YAML configs, Markdown methodology content, Next.js App Router, PowerShell ops script

---

### Task 1: Lock the 90-day onset label into the data-platform catalog

**Files:**
- Modify: `configs/data_platform/source_registry.yaml`
- Test: `src/tests/data_platform/test_catalog.py`

**Step 1: Write the failing test**

Require `gold_country_week_features` and `gold_entity_day_labels` to declare `label_onset_90d` as a required column.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/data_platform/test_catalog.py -q`

Expected: fail on missing `label_onset_90d` in the catalog contract.

**Step 3: Write minimal implementation**

Add `label_onset_90d` to the required columns for the weekly and day-label serving contracts.

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/data_platform/test_catalog.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add configs/data_platform/source_registry.yaml src/tests/data_platform/test_catalog.py
git commit -m "test: lock 90d onset label into data catalog"
```

### Task 2: Prove the weekly gold table emits `label_onset_90d`

**Files:**
- Modify: `src/tests/data_platform/test_country_week_features.py`
- Modify: `src/data_platform/serving/country_week_features.py`

**Step 1: Write the failing test**

Add assertions that `label_onset_90d` exists, becomes null when the 90-day horizon extends beyond the snapshot cutoff, and is computed with the same quiet-to-onset semantics as `label_onset_30d`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/data_platform/test_country_week_features.py::test_build_country_week_features_from_real_source_snapshots -q`

Expected: fail on missing `label_onset_90d`.

**Step 3: Write minimal implementation**

Add `future_90d_end`, `future_90d_known`, `ucdp_future_90d`, and `label_onset_90d` to the weekly label generation block and to `COUNTRY_WEEK_FEATURE_COLUMNS`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/data_platform/test_country_week_features.py::test_build_country_week_features_from_real_source_snapshots -q`

Expected: pass.

**Step 5: Commit**

```bash
git add src/tests/data_platform/test_country_week_features.py src/data_platform/serving/country_week_features.py
git commit -m "feat: add 90d onset label to weekly country features"
```

### Task 3: Propagate the 90-day onset label into the daily label export

**Files:**
- Modify: `src/tests/data_platform/test_country_week_features_pipeline.py`
- Modify: `src/data_platform/serving/entity_day_labels.py`

**Step 1: Write the failing test**

Require horizon `90` to exist in `gold_entity_day_labels`, require column `label_onset_90d`, and require non-null values for 90-day rows.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/data_platform/test_country_week_features_pipeline.py::test_country_week_features_pipeline_from_real_snapshots -q`

Expected: fail on missing horizon `90` and missing `label_onset_90d`.

**Step 3: Write minimal implementation**

Extend `ENTITY_DAY_LABEL_COLUMNS`, `_HORIZON_LABEL_COLUMNS`, and the row builder so horizon `90` maps to `label_onset_90d`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/data_platform/test_country_week_features_pipeline.py::test_country_week_features_pipeline_from_real_snapshots -q`

Expected: pass.

**Step 5: Commit**

```bash
git add src/tests/data_platform/test_country_week_features_pipeline.py src/data_platform/serving/entity_day_labels.py
git commit -m "feat: propagate 90d onset labels to day-label export"
```

### Task 4: Re-run the targeted data-platform regression slice

**Files:**
- Verify: `src/tests/data_platform/test_country_week_features.py`
- Verify: `src/tests/data_platform/test_country_week_features_pipeline.py`

**Step 1: Run the focused regression suite**

Run: `python -m pytest src/tests/data_platform/test_country_week_features.py src/tests/data_platform/test_country_week_features_pipeline.py -q`

Expected: pass.

**Step 2: Inspect the output**

Confirm the 90-day label path does not break weekly span coverage, null-handling, or day-label uniqueness.

**Step 3: If anything fails, fix the smallest cause**

Patch only the failing data-path file, not unrelated serving code.

**Step 4: Re-run the same suite**

Run the same command again and require a clean pass.

**Step 5: Commit**

```bash
git add src/tests/data_platform/test_country_week_features.py src/tests/data_platform/test_country_week_features_pipeline.py src/data_platform/serving/country_week_features.py src/data_platform/serving/entity_day_labels.py
git commit -m "test: verify 90d onset label data pipeline"
```

### Task 5: Add a checked-in test for the structural 90-day forecasting path

**Files:**
- Modify: `src/tests/forecasting/test_pipeline_integration.py`

**Step 1: Write the failing test**

Add a new integration test that expects the checked-in structural configs to train, calibrate, predict, and explain against the real weekly dataset using `label_onset_90d`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py::test_checked_in_structural_weekly_configs_support_end_to_end_pipeline -q`

Expected: fail because the structural config files do not exist yet.

**Step 3: Write minimal implementation**

Keep the test narrow: validate run names, horizon `90`, `label_onset_90d`, and `logit` as the richer model.

**Step 4: Run test to verify it still fails for the right reason**

Expected: missing config file error, not a broken test fixture.

**Step 5: Commit**

```bash
git add src/tests/forecasting/test_pipeline_integration.py
git commit -m "test: add structural 90d forecasting integration coverage"
```

### Task 6: Lock the structural-prior contract on the live 30-day onset config

**Files:**
- Modify: `src/tests/forecasting/test_pipeline_integration.py`
- Modify: `configs/forecasting/train_country_week_onset_logit_30d.yaml`
- Modify: `configs/forecasting/predict_country_week_onset_logit.yaml`

**Step 1: Write the failing test**

Require the checked-in 30-day onset config path to synthesize a structural-prior artifact and still complete train/calibrate/predict/explain.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py::test_checked_in_onset_weekly_configs_support_end_to_end_pipeline -q`

Expected: fail once the config requires a structural prior but the test does not provide one yet.

**Step 3: Write minimal implementation**

Update the test helper to create a temporary prior artifact from `label_onset_90d`, and add the `structural_prior` block to the checked-in 30-day onset train/predict configs.

**Step 4: Run test to verify it passes**

Run the same targeted test and require green.

**Step 5: Commit**

```bash
git add src/tests/forecasting/test_pipeline_integration.py configs/forecasting/train_country_week_onset_logit_30d.yaml configs/forecasting/predict_country_week_onset_logit.yaml
git commit -m "feat: feed structural prior into 30d onset trigger config"
```

### Task 7: Add the real structural 90-day training config

**Files:**
- Create: `configs/forecasting/train_country_week_onset_structural_90d.yaml`

**Step 1: Write the failing test**

Use the new structural integration test from Task 5 as the red case.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py::test_checked_in_structural_weekly_configs_support_end_to_end_pipeline -q`

Expected: fail on missing training config.

**Step 3: Write minimal implementation**

Create a structural 90-day config that uses `label_onset_90d`, horizon `90`, a mostly structural/context feature set, and `prior_rate` + `logit`.

**Step 4: Run test to verify it moves forward**

Expected: next failure should be a missing calibrate/predict/explain config, not a malformed training config.

**Step 5: Commit**

```bash
git add configs/forecasting/train_country_week_onset_structural_90d.yaml
git commit -m "feat: add structural 90d onset training config"
```

### Task 8: Add the structural 90-day calibration config

**Files:**
- Create: `configs/forecasting/calibrate_country_week_onset_structural_90d.yaml`

**Step 1: Write the failing test**

Continue using the structural integration test.

**Step 2: Run test to verify it fails**

Expected: fail on missing calibrate config.

**Step 3: Write minimal implementation**

Create the calibrate config with `run_name: country_week_onset_structural_90d`, `model_name: logit`, and isotonic calibration.

**Step 4: Run test to verify it moves forward**

Expected: fail next on missing predict or explain config.

**Step 5: Commit**

```bash
git add configs/forecasting/calibrate_country_week_onset_structural_90d.yaml
git commit -m "feat: add structural 90d onset calibration config"
```

### Task 9: Add the structural 90-day prediction config

**Files:**
- Create: `configs/forecasting/predict_country_week_onset_structural_90d.yaml`

**Step 1: Write the failing test**

Use the same structural integration test.

**Step 2: Run test to verify it fails**

Expected: fail on missing prediction config.

**Step 3: Write minimal implementation**

Mirror the structural training feature set in the prediction config and keep output name `predictions.parquet`.

**Step 4: Run test to verify it moves forward**

Expected: fail next on missing explain config or implementation issue.

**Step 5: Commit**

```bash
git add configs/forecasting/predict_country_week_onset_structural_90d.yaml
git commit -m "feat: add structural 90d onset prediction config"
```

### Task 10: Add the structural 90-day explanation config

**Files:**
- Create: `configs/forecasting/explain_country_week_onset_structural_90d.yaml`

**Step 1: Write the failing test**

Keep the structural integration test as the red case.

**Step 2: Run test to verify it fails**

Expected: fail on missing explain config.

**Step 3: Write minimal implementation**

Create the explain config with the same run/model naming conventions used elsewhere.

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py::test_checked_in_structural_weekly_configs_support_end_to_end_pipeline -q`

Expected: pass.

**Step 5: Commit**

```bash
git add configs/forecasting/explain_country_week_onset_structural_90d.yaml
git commit -m "feat: add structural 90d onset explanation config"
```

### Task 11: Add a regression test for manifest-level structural prior persistence

**Files:**
- Modify: `src/tests/forecasting/test_pipeline_integration.py`

**Step 1: Write the failing test**

Assert that the 30-day onset training manifest includes `structural_prior` metadata and that `structural_prior_score` appears in the persisted `feature_columns`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py::test_checked_in_onset_weekly_configs_support_end_to_end_pipeline -q`

Expected: fail if the manifest does not persist the prior contract.

**Step 3: Write minimal implementation**

Keep the manifest assertions precise and do not broaden the test surface unnecessarily.

**Step 4: Run test to verify it passes**

Expected: pass.

**Step 5: Commit**

```bash
git add src/tests/forecasting/test_pipeline_integration.py
git commit -m "test: verify onset manifest persists structural prior"
```

### Task 12: Add a regression test for missing structural prior at predict time

**Files:**
- Modify: `src/tests/forecasting/test_pipeline_integration.py`
- Modify: `src/forecasting/predict.py`

**Step 1: Write the failing test**

Require prediction to raise a clear error when the training manifest requires a structural prior and the prediction config omits it.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py -k structural_prior -q`

Expected: fail because the missing-prior error path is not covered or not explicit enough.

**Step 3: Write minimal implementation**

Raise a `ValueError` in `run_prediction` when the manifest has `structural_prior` but the config does not.

**Step 4: Run test to verify it passes**

Run the same filtered test selection and require green.

**Step 5: Commit**

```bash
git add src/tests/forecasting/test_pipeline_integration.py src/forecasting/predict.py
git commit -m "feat: fail fast when required structural prior is missing"
```

### Task 13: Add a regression test for structural prior feature-name mismatch

**Files:**
- Modify: `src/tests/forecasting/test_pipeline_integration.py`
- Modify: `src/forecasting/predict.py`

**Step 1: Write the failing test**

Require prediction to raise when the prediction config uses a different `feature_name` than the training manifest.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py -k structural_prior -q`

Expected: fail on missing mismatch guard.

**Step 3: Write minimal implementation**

Compare config and manifest `feature_name` values and raise a clear `ValueError` on mismatch.

**Step 4: Run test to verify it passes**

Run the same filtered selection and require green.

**Step 5: Commit**

```bash
git add src/tests/forecasting/test_pipeline_integration.py src/forecasting/predict.py
git commit -m "feat: validate structural prior feature-name consistency"
```

### Task 14: Run the focused forecasting regression slice

**Files:**
- Verify: `src/tests/forecasting/test_contracts.py`
- Verify: `src/tests/forecasting/test_pipeline_integration.py`

**Step 1: Run the targeted suite**

Run: `python -m pytest src/tests/forecasting/test_contracts.py src/tests/forecasting/test_pipeline_integration.py -q`

Expected: pass.

**Step 2: Inspect the long-running cases**

Verify the checked-in onset and structural configs both reach train/calibrate/predict/explain successfully.

**Step 3: If anything fails, patch only the smallest forecasting file**

Limit fixes to config, schema, datasets, train, or predict as indicated by the failure.

**Step 4: Re-run the same suite**

Require a clean pass before moving on.

**Step 5: Commit**

```bash
git add src/tests/forecasting/test_contracts.py src/tests/forecasting/test_pipeline_integration.py src/forecasting/schemas.py src/forecasting/datasets.py src/forecasting/train.py src/forecasting/predict.py configs/forecasting
git commit -m "test: verify structural onset forecasting path"
```

### Task 15: Add a checked-in structural 90-day backtest config

**Files:**
- Create: `configs/backtesting/country_week_onset_structural_90d.yaml`
- Test: `src/tests/backtesting/test_backtesting_integration.py`

**Step 1: Write the failing test**

Add a test that expects the checked-in structural 90-day backtest config to run on the real country-week pipeline output.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/backtesting/test_backtesting_integration.py::test_checked_in_structural_backtest_config_runs_on_real_country_week_pipeline -q`

Expected: fail on missing config.

**Step 3: Write minimal implementation**

Create the backtest config using `label_onset_90d`, horizon `90`, `prior_rate` baseline, and `logit` primary model.

**Step 4: Run test to verify it passes**

Run the same targeted test and require green.

**Step 5: Commit**

```bash
git add configs/backtesting/country_week_onset_structural_90d.yaml src/tests/backtesting/test_backtesting_integration.py
git commit -m "feat: add structural 90d onset backtest config"
```

### Task 16: Compare structural 90-day backtest metrics to the existing baseline

**Files:**
- Verify: `artifacts/backtesting/run/country_week_onset_structural_90d/*`
- Verify: `src/tests/backtesting/test_backtesting_integration.py`

**Step 1: Run the structural backtest test**

Run: `python -m pytest src/tests/backtesting/test_backtesting_integration.py::test_checked_in_structural_backtest_config_runs_on_real_country_week_pipeline -q`

Expected: pass.

**Step 2: Run the actual backtest**

Run: `python -m src.backtesting.cli run --config configs/backtesting/country_week_onset_structural_90d.yaml`

Expected: success with fresh structural backtest artifacts.

**Step 3: Inspect the summary**

Open `artifacts/backtesting/run/country_week_onset_structural_90d/summary.md` and record PR AUC, recall@10, episode recall, and false-alert burden.

**Step 4: Decide whether structural model stays prior-only or becomes a visible challenger**

If it does not beat baseline on the selected metrics, keep it internal as a prior only.

**Step 5: Commit**

```bash
git add configs/backtesting/country_week_onset_structural_90d.yaml src/tests/backtesting/test_backtesting_integration.py
git commit -m "test: verify structural onset backtest path"
```

### Task 17: Publish structural provenance in the website snapshot schema

**Files:**
- Modify: `src/website_publishing/schemas.py`
- Modify: `contracts/website_snapshot.schema.json`
- Modify: `contracts/model_card.schema.json`
- Test: `src/tests/website_publishing/test_schemas.py`

**Step 1: Write the failing test**

Require the published bundle and model card to carry optional structural provenance alongside onset and escalation provenance.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/website_publishing/test_schemas.py -q`

Expected: fail on missing structural provenance fields.

**Step 3: Write minimal implementation**

Extend the schema types so `provenance.structural` is allowed and validated.

**Step 4: Run test to verify it passes**

Run the same test and require green.

**Step 5: Commit**

```bash
git add src/website_publishing/schemas.py contracts/website_snapshot.schema.json contracts/model_card.schema.json src/tests/website_publishing/test_schemas.py
git commit -m "feat: add structural provenance to website publishing schemas"
```

### Task 18: Teach the website publisher to emit structural provenance

**Files:**
- Modify: `src/website_publishing/builder.py`
- Modify: `configs/website_publishing/site_snapshot.yaml`
- Test: `src/tests/website_publishing/test_builder.py`

**Step 1: Write the failing test**

Require the snapshot builder to read structural training/calibration/backtest artifacts and place them under `provenance.structural`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/website_publishing/test_builder.py -q`

Expected: fail on missing structural provenance.

**Step 3: Write minimal implementation**

Add optional `structural_*` config paths to the site snapshot config and include them in the builder output when present.

**Step 4: Run test to verify it passes**

Run the same test and require green.

**Step 5: Commit**

```bash
git add src/website_publishing/builder.py configs/website_publishing/site_snapshot.yaml src/tests/website_publishing/test_builder.py
git commit -m "feat: publish structural model provenance"
```

### Task 19: Re-run the website-publishing regression slice

**Files:**
- Verify: `src/tests/website_publishing/test_builder.py`
- Verify: `src/tests/website_publishing/test_schemas.py`

**Step 1: Run the targeted suite**

Run: `python -m pytest src/tests/website_publishing/test_builder.py src/tests/website_publishing/test_schemas.py -q`

Expected: pass.

**Step 2: Inspect the example snapshot**

Confirm the example bundle still validates and includes the new optional fields correctly.

**Step 3: Patch only if the schema and builder drift**

Fix the narrower side, not both blindly.

**Step 4: Re-run the same suite**

Require green again.

**Step 5: Commit**

```bash
git add src/tests/website_publishing/test_builder.py src/tests/website_publishing/test_schemas.py src/website_publishing/builder.py src/website_publishing/schemas.py configs/website_publishing/site_snapshot.yaml contracts
git commit -m "test: verify website publishing with structural provenance"
```

### Task 20: Add structural fields to the web runtime types

**Files:**
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/lib/live-snapshot.ts`
- Test: `web/src/lib/__tests__/live-snapshot.test.ts`

**Step 1: Write the failing test**

Require the live snapshot parser to ingest `provenance.structural` and keep backward compatibility with older bundles.

**Step 2: Run test to verify it fails**

Run: `npm run test:runtime`

Expected: fail on unmapped structural provenance.

**Step 3: Write minimal implementation**

Extend the web types and normalization logic to parse the new structural provenance block.

**Step 4: Run test to verify it passes**

Run: `npm run test:runtime`

Expected: pass.

**Step 5: Commit**

```bash
git add web/src/lib/types.ts web/src/lib/live-snapshot.ts web/src/lib/__tests__/live-snapshot.test.ts
git commit -m "feat: parse structural provenance in web runtime"
```

### Task 21: Surface the two-layer architecture on the homepage and status page

**Files:**
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/status/page.tsx`
- Modify: `web/src/lib/site-data-core.ts`
- Test: `web/src/lib/__tests__/site-data.test.ts`

**Step 1: Write the failing test**

Require status mapping to expose whether the live onset trigger is consuming a structural prior and to render that provenance into the operational summary.

**Step 2: Run test to verify it fails**

Run: `npm run test:runtime`

Expected: fail on unmapped structural status fields.

**Step 3: Write minimal implementation**

Add a structural-prior summary row to the status mapping and surface concise copy on `/` and `/status` without increasing urgency.

**Step 4: Run test to verify it passes**

Run: `npm run test:runtime`

Expected: pass.

**Step 5: Commit**

```bash
git add web/src/app/page.tsx web/src/app/status/page.tsx web/src/lib/site-data-core.ts web/src/lib/__tests__/site-data.test.ts
git commit -m "feat: show structural prior provenance on web surfaces"
```

### Task 22: Update the methodology pages to say the structural prior is live

**Files:**
- Modify: `web/content/methodology/backtesting.mdx`
- Modify: `web/content/methodology/model.mdx`
- Modify: `web/content/methodology/data.mdx`

**Step 1: Write the documentation checklist**

Mark the current outdated statements that still describe the structural prior as future work instead of a live layer.

**Step 2: Run content validation before changes**

Run: `npm run content:validate`

Expected: pass, but checklist still shows content drift.

**Step 3: Write minimal implementation**

Update the copy so the website accurately states that the 30-day onset trigger can consume a slower 90-day structural prior.

**Step 4: Run content validation after changes**

Run: `npm run content:validate`

Expected: pass.

**Step 5: Commit**

```bash
git add web/content/methodology/backtesting.mdx web/content/methodology/model.mdx web/content/methodology/data.mdx
git commit -m "docs: describe live structural prior architecture"
```

### Task 23: Update the model card template and example artifacts for the two-layer system

**Files:**
- Modify: `docs/model_card_template.md`
- Modify: `artifacts/examples/website_snapshot_example.json`
- Modify: `contracts/model_card.schema.json`

**Step 1: Write the failing checklist**

Confirm the model card template does not yet mention structural provenance, prior-vs-trigger layering, or structural-only metrics.

**Step 2: Run validation where applicable**

Run any existing schema validation or content validation that covers these artifacts.

**Step 3: Write minimal implementation**

Add fields and examples for structural provenance, prior feature usage, and model-layer roles.

**Step 4: Re-run validation**

Require the updated example to remain schema-valid.

**Step 5: Commit**

```bash
git add docs/model_card_template.md artifacts/examples/website_snapshot_example.json contracts/model_card.schema.json
git commit -m "docs: align model card artifacts with two-layer forecasting"
```

### Task 24: Re-run web content validation after methodology and artifact changes

**Files:**
- Verify: `web/content/methodology/*`
- Verify: `artifacts/examples/website_snapshot_example.json`

**Step 1: Run validation**

Run: `npm run content:validate`

Expected: pass.

**Step 2: Inspect warnings**

If content validation passes with warnings, fix the exact page or frontmatter drift.

**Step 3: Re-run validation**

Require a clean pass.

**Step 4: Note the result in the work log**

Capture that methodology content is aligned with the live structural stack.

**Step 5: Commit**

```bash
git add web/content/methodology docs/model_card_template.md artifacts/examples/website_snapshot_example.json
git commit -m "test: validate methodology and model card content"
```

### Task 25: Align `report_inputs` with onset-first monitoring semantics

**Files:**
- Modify: `src/data_platform/serving/report_inputs.py`
- Test: `src/tests/data_platform/test_report_inputs.py`

**Step 1: Write the failing test**

Require report inputs to suppress artificial urgency when the latest label state is incomplete or effectively monitoring-only.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/data_platform/test_report_inputs.py -q`

Expected: fail on old heuristic behavior.

**Step 3: Write minimal implementation**

Adjust `latest_label_targets_are_known()` and score-to-risk labeling so no-clear-leader style rows do not get promoted into fake critical language.

**Step 4: Run test to verify it passes**

Run the same test and require green.

**Step 5: Commit**

```bash
git add src/data_platform/serving/report_inputs.py src/tests/data_platform/test_report_inputs.py
git commit -m "feat: tone down report inputs in monitoring states"
```

### Task 26: Align `social_inputs` with no-clear-leader semantics

**Files:**
- Modify: `src/data_platform/serving/social_inputs.py`
- Test: `src/tests/data_platform/test_social_inputs.py`

**Step 1: Write the failing test**

Require social export rows to avoid decisive language when there is no clear leader or when the latest weekly row is incomplete.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/data_platform/test_social_inputs.py -q`

Expected: fail on old urgency assumptions.

**Step 3: Write minimal implementation**

Keep the social builder deterministic, but use monitoring-grade summary lines when signal separation is weak.

**Step 4: Run test to verify it passes**

Run the same test and require green.

**Step 5: Commit**

```bash
git add src/data_platform/serving/social_inputs.py src/tests/data_platform/test_social_inputs.py
git commit -m "feat: align social inputs with no-clear-leader state"
```

### Task 27: Re-run the report/social serving-layer verification

**Files:**
- Verify: `src/tests/data_platform/test_report_inputs.py`
- Verify: `src/tests/data_platform/test_social_inputs.py`

**Step 1: Run the focused suite**

Run: `python -m pytest src/tests/data_platform/test_report_inputs.py src/tests/data_platform/test_social_inputs.py -q`

Expected: pass.

**Step 2: Inspect the generated text**

Confirm the outputs are institutional and restrained rather than AI-style dramatic.

**Step 3: If needed, patch the exact formatter logic**

Keep changes minimal and deterministic.

**Step 4: Re-run the same suite**

Require green.

**Step 5: Commit**

```bash
git add src/tests/data_platform/test_report_inputs.py src/tests/data_platform/test_social_inputs.py src/data_platform/serving/report_inputs.py src/data_platform/serving/social_inputs.py
git commit -m "test: verify monitoring semantics in report and social outputs"
```

### Task 28: Add structural artifact freshness to `/api/health`

**Files:**
- Modify: `web/src/app/api/health/route.ts`
- Modify: `web/src/lib/site-data-core.ts`
- Test: `web/src/lib/__tests__/site-data.test.ts`

**Step 1: Write the failing test**

Require the health payload to expose whether a structural prior artifact is present and when it was last published.

**Step 2: Run test to verify it fails**

Run: `npm run test:runtime`

Expected: fail on missing health fields.

**Step 3: Write minimal implementation**

Read structural provenance from the snapshot bundle and attach a compact status object to `/api/health`.

**Step 4: Run test to verify it passes**

Run: `npm run test:runtime`

Expected: pass.

**Step 5: Commit**

```bash
git add web/src/app/api/health/route.ts web/src/lib/site-data-core.ts web/src/lib/__tests__/site-data.test.ts
git commit -m "feat: expose structural artifact freshness in health API"
```

### Task 29: Add the structural backtest to backend refresh automation

**Files:**
- Modify: `scripts/run_backend_refresh.ps1`

**Step 1: Write the failing checklist**

Confirm the refresh script currently misses the structural train/calibrate/predict stage or does not run it before the onset trigger.

**Step 2: Run the current script once**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_backend_refresh.ps1`

Expected: succeed without structural stage, proving the checklist gap is real.

**Step 3: Write minimal implementation**

Insert structural train/calibrate/predict steps before the onset trigger steps and keep the log labels explicit.

**Step 4: Run the script again**

Require a successful refresh with structural artifacts written before the onset trigger run.

**Step 5: Commit**

```bash
git add scripts/run_backend_refresh.ps1
git commit -m "feat: run structural prior stage in backend refresh"
```

### Task 30: Verify the refresh produces the structural prior artifact and onset manifest wiring

**Files:**
- Verify: `artifacts/forecasting/predict/country_week_onset_structural_90d/predictions.parquet`
- Verify: `artifacts/forecasting/train/country_week_onset_logit_30d/manifest.json`

**Step 1: Run the refresh**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_backend_refresh.ps1`

Expected: success.

**Step 2: Inspect the structural artifact**

Confirm the structural prediction file exists and uses the expected run name.

**Step 3: Inspect the onset manifest**

Confirm `structural_prior_score` appears in `feature_columns` and that `structural_prior` metadata is present.

**Step 4: If anything is missing, patch the narrowest source**

Fix config, script ordering, or manifest persistence exactly where needed.

**Step 5: Commit**

```bash
git add scripts/run_backend_refresh.ps1 configs/forecasting src/forecasting
git commit -m "test: verify structural prior is wired into refresh artifacts"
```

### Task 31: Re-run the website publishing after the structural refresh

**Files:**
- Verify: `artifacts/website_publishing/site_snapshot/latest/*`
- Modify: `configs/website_publishing/site_snapshot.yaml` if needed

**Step 1: Run publish through the refresh path**

Use the refresh script from Task 29.

**Step 2: Inspect the site snapshot**

Confirm the latest bundle still reports `primary_target: onset`, still carries the structural provenance block, and still abstains honestly if the model remains monitoring-only.

**Step 3: Fix the publisher only if the structural provenance is missing**

Do not change website semantics just to force a sharper alert.

**Step 4: Re-run publish**

Require the updated bundle to be written successfully.

**Step 5: Commit**

```bash
git add configs/website_publishing/site_snapshot.yaml src/website_publishing
git commit -m "test: verify published snapshot after structural refresh"
```

### Task 32: Run the full backend and forecasting verification slice

**Files:**
- Verify: `src/tests/forecasting`
- Verify: `src/tests/backtesting`
- Verify: `src/tests/website_publishing`
- Verify: `src/tests/data_platform`

**Step 1: Run forecasting and publishing tests**

Run: `python -m pytest src/tests/forecasting src/tests/website_publishing -q`

Expected: pass.

**Step 2: Run data-platform tests**

Run: `python -m pytest src/tests/data_platform -q`

Expected: pass.

**Step 3: Run the targeted backtesting tests**

Run: `python -m pytest src/tests/backtesting/test_backtesting_integration.py src/tests/backtesting/test_engine_and_reports.py -q`

Expected: pass.

**Step 4: Fix the smallest verified regression only**

Do not broaden scope beyond the failing component.

**Step 5: Commit**

```bash
git add src/tests src/data_platform src/forecasting src/backtesting src/website_publishing
git commit -m "test: run backend verification slice for release"
```

### Task 33: Run the full web verification sweep

**Files:**
- Verify: `web/src/*`
- Verify: `web/content/*`

**Step 1: Run runtime tests**

Run: `npm run test:runtime`

Expected: pass.

**Step 2: Run content validation**

Run: `npm run content:validate`

Expected: pass.

**Step 3: Run lint and build**

Run:

```bash
npm run lint
npm run build
```

Expected: pass, with only the known non-blocking Turbopack NFT warning unless it gets fixed separately.

**Step 4: Patch only if a real regression appears**

Do not spend time on the existing non-blocking NFT warning unless it changes behavior.

**Step 5: Commit**

```bash
git add web
git commit -m "test: run full web verification sweep"
```

### Task 34: Do browser-based visual QA on the key routes

**Files:**
- Verify: `/`
- Verify: `/status`
- Verify: `/methodology`
- Verify: `/countries/australia`
- Verify: `/forecasts`

**Step 1: Start the local site if needed**

Run the local web app and confirm it serves the refreshed snapshot.

**Step 2: Open the core routes**

Use the browser tools to inspect the homepage, status page, methodology pages, and at least one arbitrary country route generated from the live snapshot.

**Step 3: Capture screenshots**

Save evidence for any layout or messaging regressions.

**Step 4: Fix only real UX regressions**

Focus on copy drift, missing structural provenance, stale timestamps, or false urgency.

**Step 5: Commit**

```bash
git add web/src/app web/src/components web/src/lib
git commit -m "fix: resolve visual regressions in final release sweep"
```

### Task 35: Write the final release summary and residual-risk note

**Files:**
- Modify: `docs/current_state.md`
- Modify: `final.md`
- Verify: `artifacts/ops/backend-refresh-*.log`

**Step 1: Write the release checklist**

Capture the final accepted state: onset-first, structural prior live, website publishing honest, verification complete, and remaining known warnings/risks.

**Step 2: Update the status docs**

Record the final refresh timestamp, current snapshot state, model promotion status, and remaining limitations.

**Step 3: Verify the final evidence**

Quote the exact successful verification commands and the latest refresh log path.

**Step 4: Re-read the summary for truthfulness**

Make sure it does not claim predictive maturity beyond what the current backtests support.

**Step 5: Commit**

```bash
git add docs/current_state.md final.md
git commit -m "docs: finalize release state and residual risks"
```
