# Remaining Production Milestone Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the post-baseline production milestone after the dense `country_week_features` work by publishing downstream gold tables, strengthening the real weekly forecasting and backtesting paths, and wiring the website to generated artifacts.

**Architecture:** The weekly gold table is now dense, includes `country_name` and `region_name`, and is the single source of truth for downstream serving work. The remaining implementation should derive thin, useful serving contracts from that table first, then improve model training and reporting on top of the denser history, and only then switch the website from demo/static content to artifact-backed loaders. Do not reopen Task 1 unless a downstream change breaks its verified behavior.

**Tech Stack:** Python 3.11, Pandas, Parquet, Pytest, YAML configs, scikit-learn, LightGBM, Next.js App Router, TypeScript, MDX

---

## Current Starting Point

- Verified on `2026-03-27`: `country_week_features` is dense and written at `data/gold/country_week_features/country_week_features.parquet`.
- Verified row shape: `17,580` rows, `30` countries, `586` weekly rows per country, `2015-01-05` through `2026-03-23`.
- Verified commands already green:
  - `python -m pytest src/tests/data_platform -q`
  - `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml --use-test-snapshots`

## Batch Order

1. Task 1 below: downstream gold tables
2. Task 2 below: richer real forecasting
3. Task 3 below: multi-model backtesting
4. Task 4 below: website artifact wiring
5. Task 5 below: social publishing, only after Tasks 1-4 are green

Stop after each task-level verification and record any contract changes before moving on.

## Task 1: Publish Downstream Gold Tables

**Files:**
- Create: `src/data_platform/serving/entity_day_features.py`
- Create: `src/data_platform/serving/entity_day_labels.py`
- Create: `src/data_platform/serving/report_inputs.py`
- Create: `src/data_platform/serving/social_inputs.py`
- Modify: `src/data_platform/orchestration/pipeline.py`
- Modify: `src/data_platform/schemas.py`
- Modify: `configs/data_platform/source_registry.yaml`
- Modify: `docs/data_platform.md`
- Modify: `src/tests/data_platform/test_country_week_features_pipeline.py`
- Create: `src/tests/data_platform/test_report_inputs.py`
- Create: `src/tests/data_platform/test_social_inputs.py`

**Implementation notes:**
- Keep the first version thin and derived from the dense weekly table. Do not invent a finer entity grain than the data supports.
- Use `country_iso3` as the initial entity identifier for all four tables.
- Add new gold output paths to `CountryWeekPipelineRunResult` in `src/data_platform/schemas.py` so tests can assert them directly.

**Step 1:** Write failing pipeline assertions in `src/tests/data_platform/test_country_week_features_pipeline.py` for four new parquet outputs plus four new validation reports.

Run:
- `python -m pytest src/tests/data_platform/test_country_week_features_pipeline.py -q`

**Step 2:** Write failing unit tests for `report_inputs` and `social_inputs`.

Minimum contract to lock down:
- `gold_entity_day_features`: `entity_id`, `entity_type`, `country_iso3`, `country_name`, `feature_date`, `source_week_start_date`
- `gold_entity_day_labels`: `entity_id`, `country_iso3`, `label_date`, `horizon_days`, implemented label columns
- `gold_report_inputs`: `country_iso3`, `country_name`, `region_name`, `report_date`, `risk_level`, `freshness_days`, `summary`, `chronology`
- `gold_social_inputs`: `country_iso3`, `country_name`, `publish_date`, `score_delta`, `summary_line`, `top_drivers`, `report_slug`

Run:
- `python -m pytest src/tests/data_platform/test_report_inputs.py src/tests/data_platform/test_social_inputs.py -q`

**Step 3:** Implement `entity_day_features.py`.

Approach:
- Expand each dense weekly row into seven daily rows ending on `week_start_date + 6d`
- Preserve a `source_week_start_date` pointer
- Carry through a small, stable feature subset needed by downstream consumers first
- Set `entity_type = "country"`

**Step 4:** Implement `entity_day_labels.py`.

Approach:
- Expand implemented weekly labels to daily rows aligned to the same seven-day span
- Preserve `horizon_days` explicitly for each exported label set
- Keep null labels where the weekly source row is genuinely unknown

**Step 5:** Implement `report_inputs.py` and `social_inputs.py`.

Approach:
- Start from the latest available weekly row per country
- Build deterministic first-cut summaries from existing values rather than forecast artifacts
- Keep `chronology` and `top_drivers` as compact serialized lists/strings if a richer schema would slow delivery
- Use a placeholder slug format like `<country_iso3-lower>-latest`

**Step 6:** Extend `src/data_platform/orchestration/pipeline.py` to write the four new gold tables under `data/gold/` and add validation entries for each table.

Run:
- `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml --use-test-snapshots`

**Step 7:** Update `configs/data_platform/source_registry.yaml` and `docs/data_platform.md` to mark the contracts as implemented and document their minimal schemas.

**Step 8:** Re-run the full data-platform suite.

Run:
- `python -m pytest src/tests/data_platform -q`

## Task 2: Strengthen Real Forecasting Beyond The Baseline

**Files:**
- Modify: `src/forecasting/train.py`
- Modify: `src/forecasting/metrics.py`
- Modify: `src/forecasting/predict.py`
- Modify: `src/forecasting/explain.py`
- Modify: `src/forecasting/datasets.py`
- Modify: `docs/forecasting.md`
- Create: `configs/forecasting/train_country_week_logit_30d.yaml`
- Create: `configs/forecasting/train_country_week_lightgbm_30d.yaml`
- Create: `configs/forecasting/predict_country_week_logit.yaml`
- Modify: `src/tests/forecasting/test_pipeline_integration.py`

**Implementation notes:**
- Keep `train_country_week_30d.yaml` and `prior_rate` untouched as the safe fallback.
- The richer path must degrade gracefully when folds have too few positives.
- If the current repo needs schema or registry support for a new model name, modify `src/forecasting/models.py` or `src/forecasting/schemas.py` in the same task rather than layering ad hoc conditionals.

**Step 1:** Add failing integration tests in `src/tests/forecasting/test_pipeline_integration.py`.

Lock down:
- logistic regression runs on the real weekly table when fold class counts are sufficient
- untrainable folds are skipped and recorded instead of crashing
- metric outputs remain defined when only one class is present

Run:
- `python -m pytest src/tests/forecasting/test_pipeline_integration.py -q`

**Step 2:** Implement fold-trainability checks in `src/forecasting/train.py` and supporting metric notes in `src/forecasting/metrics.py`.

Minimum behavior:
- check positive and negative class counts per fold before fitting
- skip invalid folds cleanly
- persist which folds were skipped and why

**Step 3:** Ensure `predict.py` and `explain.py` can consume training runs with skipped folds without assuming every fold produced a model artifact.

**Step 4:** Add the new config files.

Required configs:
- `configs/forecasting/train_country_week_logit_30d.yaml`
- `configs/forecasting/train_country_week_lightgbm_30d.yaml`
- `configs/forecasting/predict_country_week_logit.yaml`

**Step 5:** Run the richer real forecasting chain on the logistic configuration first.

Run:
- `python -m src.forecasting.train --config configs/forecasting/train_country_week_logit_30d.yaml`
- `python -m src.forecasting.calibrate --config configs/forecasting/calibrate_country_week.yaml --training-run-dir <train_run_dir>`
- `python -m src.forecasting.predict --config configs/forecasting/predict_country_week_logit.yaml --training-run-dir <train_run_dir> --calibration-run-dir <calibration_run_dir>`
- `python -m src.forecasting.explain --config configs/forecasting/explain_country_week.yaml --training-run-dir <train_run_dir> --prediction-file <prediction_file>`

**Step 6:** Update `docs/forecasting.md` with the baseline-vs-richer-model guidance and the skipped-fold behavior.

**Step 7:** Re-run forecasting tests.

Run:
- `python -m pytest src/tests/forecasting -q`

## Task 3: Strengthen Backtesting Reports And Comparisons

**Files:**
- Modify: `src/backtesting/engine.py`
- Modify: `src/backtesting/evaluators.py`
- Modify: `src/backtesting/reports.py`
- Modify: `docs/backtesting.md`
- Create: `configs/backtesting/country_week_logit.yaml`
- Modify: `src/tests/backtesting/test_backtesting_integration.py`

**Implementation notes:**
- Compare the richer logistic model against the existing `prior_rate` baseline.
- Keep replay working on the current single-entity flow.
- If the current config loader cannot express multi-model comparison cleanly, update `src/backtesting/schemas.py` and `src/backtesting/experiments.py` in the same task.

**Step 1:** Add failing tests in `src/tests/backtesting/test_backtesting_integration.py`.

Lock down:
- report output includes baseline vs richer model comparison
- markdown contains one summary block per model
- replay still loads after the comparison changes

Run:
- `python -m pytest src/tests/backtesting/test_backtesting_integration.py -q`

**Step 2:** Extend `engine.py` and `evaluators.py` so a single run can summarize both models cleanly.

**Step 3:** Extend `reports.py` to emit:
- explicit baseline comparison section
- top-performing model summary
- plot references
- calibration note
- alert-burden note

**Step 4:** Add `configs/backtesting/country_week_logit.yaml`.

**Step 5:** Run both backtest flows plus replay.

Run:
- `python -m src.backtesting.cli run --config configs/backtesting/country_week.yaml`
- `python -m src.backtesting.cli run --config configs/backtesting/country_week_logit.yaml`
- `python -m src.backtesting.cli replay --config configs/backtesting/replay_iran.yaml`

**Step 6:** Update `docs/backtesting.md`.

**Step 7:** Re-run backtesting tests.

Run:
- `python -m pytest src/tests/backtesting -q`

## Task 4: Wire The Website To Real Forecast And Backtest Artifacts

**Files:**
- Create: `web/src/lib/artifacts.ts`
- Modify: `web/src/lib/site-data.ts`
- Modify: `web/src/lib/content.ts`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/forecasts/page.tsx`
- Modify: `web/src/app/countries/page.tsx`
- Modify: `web/src/app/countries/[slug]/page.tsx`
- Modify: `web/src/components/forecast-explorer.tsx`
- Modify: `web/src/components/monitor-table.tsx`
- Modify: `web/scripts/validate-content.mjs`

**Implementation notes:**
- Prefer a single artifact-loading layer in `web/src/lib/artifacts.ts`.
- Read from `artifacts/forecasting_real_check2/` and `artifacts/backtesting_real_check/`.
- Keep a local demo fallback only when artifact files are missing or unreadable.
- Do not hard-code featured countries.

**Step 1:** Add a file-loader abstraction in `web/src/lib/artifacts.ts`.

Responsibilities:
- locate the latest prediction and backtest artifacts
- parse the minimum fields needed by the web app
- return `null` or demo fallback tokens when files are missing

**Step 2:** Refactor `web/src/lib/site-data.ts` and `web/src/lib/content.ts` to use artifact-backed loaders first and static/demo data second.

**Step 3:** Update the page entrypoints and components to consume the new loader output.

Minimum outcomes:
- homepage featured pair from real predictions
- forecasts page / monitor table from real predictions
- country page dossier metrics from real predictions plus backtest summaries

**Step 4:** Update `web/scripts/validate-content.mjs` so artifact-backed content checks do not fail when the fallback path is intentionally used.

**Step 5:** Run website verification.

Run:
- `npm run content:validate`
- `npm run lint`
- `npm run build`

## Task 5: Social Publishing, Gated After Tasks 1-4

**Files:**
- Create: `src/social_publishing/`
- Modify: `docs/current_state.md`
- Modify: `../final.md`

**Hard gate:** Do not start this task until Tasks 1-4 are green in the same session or the immediately preceding verified session.

**Step 1:** Create the package skeleton under `src/social_publishing/`.

Minimum modules:
- formatter
- review queue/export helper
- dry-run CLI or script entrypoint

**Step 2:** Use `gold_social_inputs` as the only input contract.

Do not read directly from website files or raw forecast artifacts in this first version.

**Step 3:** Keep v1 simple.

Required behavior:
- format candidate posts
- persist a reviewable dry-run export
- no live posting integration yet

**Step 4:** Update `docs/current_state.md` and `../final.md` with the new factual state only after the implementation and verification are complete.

## Finish Commands

Run all of these before closing the execution session:

- `python -m pytest src/tests/data_platform src/tests/forecasting src/tests/backtesting -q`
- `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml --use-test-snapshots`
- `python -m src.forecasting.train --config configs/forecasting/train_country_week_30d.yaml`
- `python -m src.backtesting.cli run --config configs/backtesting/country_week.yaml`
- `npm run content:validate`
- `npm run lint`
- `npm run build`
