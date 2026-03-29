# Next Steps Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the current real weekly baseline into the next production-grade milestone: denser data serving tables, stronger real forecasting/backtesting, and website wiring to generated artifacts instead of static content.

**Architecture:** The repo now has a real `country_week_features` gold table, a real forecasting path on top of that table, a working backtesting package, and an automated website hero. The next session should not rebuild those foundations. It should expand the weekly data contract into denser downstream serving tables, improve the real model path beyond the sparse baseline-first setup, and then wire the website to those generated artifacts.

**Tech Stack:** Python 3.11 target, Pandas, Parquet, Pytest, YAML configs, LightGBM / scikit-learn, Next.js App Router, TypeScript, MDX

---

## Current Baseline

Read these first in the new session:

- `final.md`
- `georisk/docs/current_state.md`
- `georisk/docs/data_platform.md`
- `georisk/docs/forecasting.md`
- `georisk/docs/backtesting.md`

Already implemented:

- Phase A weekly master table in `georisk/data/gold/country_week_features/country_week_features.parquet`
- Forecasting on real `country_week_features`
- Backtesting CLI with `run` and `replay`
- Website hero auto-selects the current highest-stress countries

Do not spend the next session redoing:

- homepage design exploration
- source-registry work already reflected in `configs/data_platform/source_registry.yaml`
- synthetic `country_day` work as the main path

## Task 1: Densify The Weekly Master Table

**Files:**
- Create: `georisk/src/data_platform/serving/panel.py`
- Modify: `georisk/src/data_platform/serving/country_week_features.py`
- Modify: `georisk/src/data_platform/orchestration/pipeline.py`
- Modify: `georisk/src/data_platform/countries.py`
- Modify: `georisk/src/data_platform/schemas.py`
- Test: `georisk/src/tests/data_platform/test_country_week_features.py`
- Test: `georisk/src/tests/data_platform/test_country_week_features_pipeline.py`

**Step 1:** Write failing tests for a dense panel contract.

Expected additions:
- `country_name`
- `region_name`
- continuous country-week rows over the configured date span
- zero-filled event counts where no events occurred
- carried-forward annual / snapshot features where appropriate

Run:
- `python -m pytest src/tests/data_platform/test_country_week_features.py -q`

**Step 2:** Create panel helpers in `serving/panel.py`.

Implement:
- weekly date index builder
- country dimension builder from known ISO3 values
- dense cartesian country-week panel generator

**Step 3:** Refactor `build_country_week_features()` to join sparse aggregates onto the dense panel.

Rules:
- event-style blocks: zero-fill count columns
- annual/snapshot blocks: latest available observation up to that week
- labels: preserve null only where the forward window is genuinely unknowable
- add `country_name` and `region_name` to the gold table

**Step 4:** Run the pipeline against snapshots and inspect row growth.

Run:
- `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml --use-test-snapshots`

**Step 5:** Re-run all data-platform tests.

Run:
- `python -m pytest src/tests/data_platform -q`

## Task 2: Publish The Missing Downstream Gold Tables

**Files:**
- Create: `georisk/src/data_platform/serving/entity_day_features.py`
- Create: `georisk/src/data_platform/serving/entity_day_labels.py`
- Create: `georisk/src/data_platform/serving/report_inputs.py`
- Create: `georisk/src/data_platform/serving/social_inputs.py`
- Modify: `georisk/src/data_platform/orchestration/pipeline.py`
- Modify: `georisk/configs/data_platform/source_registry.yaml`
- Modify: `georisk/docs/data_platform.md`
- Test: `georisk/src/tests/data_platform/test_country_week_features_pipeline.py`
- Create: `georisk/src/tests/data_platform/test_report_inputs.py`
- Create: `georisk/src/tests/data_platform/test_social_inputs.py`

**Step 1:** Add failing tests for the new gold outputs.

Minimum contracts:
- `gold_entity_day_features`
- `gold_entity_day_labels`
- `gold_report_inputs`
- `gold_social_inputs`

**Step 2:** Implement the smallest useful versions of those tables.

First-cut expectations:
- `entity_day_features`: country-level daily or pseudo-daily serving rows if no finer entity grain exists yet
- `entity_day_labels`: align to implemented forecast targets and horizons
- `report_inputs`: country summary, main drivers, risk ladder, freshness, reportable chronology slice
- `social_inputs`: country, score delta, one-line summary, top drivers, report URL slug placeholder

**Step 3:** Extend the pipeline so these tables are written under `data/gold/`.

Add validation reports for each.

**Step 4:** Re-run pipeline and tests.

Run:
- `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml --use-test-snapshots`
- `python -m pytest src/tests/data_platform -q`

## Task 3: Strengthen Real Forecasting Beyond The Sparse Baseline

**Files:**
- Modify: `georisk/src/forecasting/train.py`
- Modify: `georisk/src/forecasting/metrics.py`
- Modify: `georisk/src/forecasting/predict.py`
- Modify: `georisk/src/forecasting/explain.py`
- Modify: `georisk/src/forecasting/datasets.py`
- Modify: `georisk/docs/forecasting.md`
- Create: `georisk/configs/forecasting/train_country_week_logit_30d.yaml`
- Create: `georisk/configs/forecasting/train_country_week_lightgbm_30d.yaml`
- Create: `georisk/configs/forecasting/predict_country_week_logit.yaml`
- Test: `georisk/src/tests/forecasting/test_pipeline_integration.py`

**Step 1:** Add failing tests for richer real-country-week model configs.

Focus:
- logistic regression runs cleanly on the real weekly table when enough class variation exists
- training skips invalid folds gracefully instead of failing noisily
- metrics stay well-defined on low-positive windows

**Step 2:** Add model-selection safeguards.

Implement:
- minimum class-count checks per fold
- skip / record folds that are not trainable
- explicit metric notes when only one class is present

**Step 3:** Add richer real configs.

At minimum:
- one logistic config
- one LightGBM config
- keep `prior_rate` as the safe baseline

**Step 4:** Run the real forecasting chain for the richer config that the data currently supports.

Run:
- `python -m src.forecasting.train --config configs/forecasting/train_country_week_logit_30d.yaml`
- `python -m src.forecasting.calibrate --config configs/forecasting/calibrate_country_week.yaml --training-run-dir <train_run_dir>`
- `python -m src.forecasting.predict --config configs/forecasting/predict_country_week_logit.yaml --training-run-dir <train_run_dir> --calibration-run-dir <calibration_run_dir>`
- `python -m src.forecasting.explain --config configs/forecasting/explain_country_week.yaml --training-run-dir <train_run_dir> --prediction-file <prediction_file>`

**Step 5:** Re-run forecasting tests.

Run:
- `python -m pytest src/tests/forecasting -q`

## Task 4: Strengthen Backtesting Reports And Comparisons

**Files:**
- Modify: `georisk/src/backtesting/engine.py`
- Modify: `georisk/src/backtesting/evaluators.py`
- Modify: `georisk/src/backtesting/reports.py`
- Modify: `georisk/docs/backtesting.md`
- Create: `georisk/configs/backtesting/country_week_logit.yaml`
- Test: `georisk/src/tests/backtesting/test_backtesting_integration.py`

**Step 1:** Add failing tests for multi-model comparison reporting.

Need:
- baseline vs richer model comparison
- per-model summary in metrics and markdown
- replay still works after multi-model output

**Step 2:** Extend backtest reporting.

Add:
- explicit baseline comparison section
- top-performing-model summary
- plot references in markdown
- calibration and alert-burden notes

**Step 3:** Add a second backtest config for the richer weekly model path.

**Step 4:** Run both backtesting flows.

Run:
- `python -m src.backtesting.cli run --config configs/backtesting/country_week.yaml`
- `python -m src.backtesting.cli run --config configs/backtesting/country_week_logit.yaml`
- `python -m src.backtesting.cli replay --config configs/backtesting/replay_iran.yaml`

**Step 5:** Re-run backtesting tests.

Run:
- `python -m pytest src/tests/backtesting -q`

## Task 5: Wire The Website To Real Forecast And Backtest Artifacts

**Files:**
- Create: `georisk/web/src/lib/artifacts.ts`
- Modify: `georisk/web/src/lib/site-data.ts`
- Modify: `georisk/web/src/lib/content.ts`
- Modify: `georisk/web/src/app/page.tsx`
- Modify: `georisk/web/src/app/forecasts/page.tsx`
- Modify: `georisk/web/src/app/countries/page.tsx`
- Modify: `georisk/web/src/app/countries/[slug]/page.tsx`
- Modify: `georisk/web/src/components/forecast-explorer.tsx`
- Modify: `georisk/web/src/components/monitor-table.tsx`
- Test: `georisk/web/scripts/validate-content.mjs`

**Step 1:** Add a file-loader layer for the latest forecast and backtest artifacts.

Read from:
- `artifacts/forecasting_real_check2/`
- `artifacts/backtesting_real_check/`

Do not hard-code countries.

**Step 2:** Replace static homepage / monitor / forecast-board sourcing with artifact-backed loaders.

Minimum result:
- homepage featured pair from real predictions
- monitor table from real predictions
- country dossier metrics from real prediction + backtest summaries

**Step 3:** Keep demo fallback only if artifact files are missing locally.

**Step 4:** Run website checks.

Run:
- `npm run content:validate`
- `npm run lint`
- `npm run build`

## Task 6: Social Publishing After Artifact Wiring

**Files:**
- Create: `georisk/src/social_publishing/`
- Modify: `georisk/docs/current_state.md`
- Modify: `final.md`

**Step 1:** Do not start this until Tasks 1-5 are green.

**Step 2:** Use `gold_social_inputs` as the only input contract.

**Step 3:** Keep first implementation simple:
- post formatting
- review queue
- dry-run export

## Acceptance Check For The Next Session

The next session should stop only after these are true:

1. `country_week_features` is denser and includes country naming / region metadata
2. downstream gold tables exist for reports and social
3. richer real forecasting configs run cleanly beside the baseline
4. backtesting compares models and writes clearer reports
5. the website reads generated forecast / backtest artifacts instead of relying on static demo country data

## Commands To Finish With

Run all of these before closing the next session:

- `python -m pytest src/tests/data_platform src/tests/forecasting src/tests/backtesting -q`
- `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml --use-test-snapshots`
- `python -m src.forecasting.train --config configs/forecasting/train_country_week_30d.yaml`
- `python -m src.backtesting.cli run --config configs/backtesting/country_week.yaml`
- `npm run content:validate`
- `npm run lint`
- `npm run build`
