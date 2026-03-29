# Core Data, Backtesting, and Forecasting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the prompt-aligned Phase A model stack by finishing the mandatory data layer, training forecasting on real platform tables, and implementing backtesting so forecasting can be treated as complete.

**Architecture:** The current repo already has a forecasting scaffold, a partial real-source data layer, and no backtesting package. This plan treats `06_data_sources_catalog.md` Phase A as the practical definition of a "complete data layer" for v1, then uses those gold tables as the only supported inputs to the forecasting and backtesting layers.

**Tech Stack:** Python 3.11 target, Pandas, Parquet, Pytest, YAML configs, LightGBM, plotting/report generation in Python

---

### Task 1: Lock the Phase A data-layer contract

**Files:**
- Modify: `docs/data_platform.md`
- Modify: `docs/current_state.md`
- Modify: `src/data_platform/schemas.py`
- Create: `src/data_platform/catalog.py`
- Create: `configs/data_platform/source_registry.yaml`

**Step 1:** Define the explicit Phase A mandatory source set from `06_data_sources_catalog.md`:
- `ACLED`
- `UCDP GED`
- `GDELT`
- `UNHCR`
- `WDI`
- `IMF`
- `FAO`
- `V-Dem` or `WGI`
- `IDEA`
- `SIPRI`
- `UNCTAD`
- `NOAA`
- `NASA Black Marble`
- `UN Comtrade`

**Step 2:** Add a source registry that marks each source as:
- `implemented`
- `stubbed`
- `missing`
- `account_required`
- `snapshot_required`

**Step 3:** Define the v1 serving contracts that downstream code must use:
- `gold_country_week_features`
- `gold_entity_day_features`
- `gold_entity_day_labels`
- `gold_report_inputs`
- `gold_social_inputs`

**Step 4:** Run schema-level tests after the registry and contracts are added.

Run:
- `python -m pytest src/tests/data_platform -q`

### Task 2: Finish the missing Phase A source connectors

**Files:**
- Modify: `src/data_platform/ingestion/*`
- Modify: `src/data_platform/normalization/*`
- Modify: `src/data_platform/orchestration/pipeline.py`
- Modify: `src/data_platform/validation/*`
- Test: `src/tests/data_platform/*`
- Create fixtures under: `src/tests/fixtures/real_source/*`

**Step 1:** Implement the highest-priority missing event source:
- `ACLED`

**Step 2:** Implement the remaining Phase A structural and macro sources that can be integrated with open or documented-access workflows:
- `IMF`
- `FAO`
- `WGI` or `V-Dem`
- `IDEA`
- `UNCTAD`
- `NOAA`
- `UN Comtrade`

**Step 3:** Add placeholder or snapshot-driven adapters for slower-moving but still required sources:
- `SIPRI`
- `NASA Black Marble`

**Step 4:** Leave `BIS` as a tracked follow-on only if it is explicitly retained outside the prompt-required Phase A MVP definition.

**Step 5:** Add integration tests for each new connector and one end-to-end pipeline test that covers multi-source gold publication.

Run:
- `python -m pytest src/tests/data_platform -q`

### Task 3: Expand the gold tables to catalog-level feature families

**Files:**
- Modify: `src/data_platform/serving/country_week_features.py`
- Create: `src/data_platform/serving/entity_day_features.py`
- Create: `src/data_platform/serving/entity_day_labels.py`
- Create: `src/data_platform/serving/report_inputs.py`
- Create: `src/data_platform/serving/social_inputs.py`
- Modify: `configs/data_platform/pipeline_country_week_features.yaml`
- Create: additional serving configs under `configs/data_platform/`

**Step 1:** Expand `country_week_features` so it contains the feature blocks called out in `06_data_sources_catalog.md`:
- `acled_*`
- `ucdp_history_*`
- `gdelt_*`
- `macro_*`
- `food_*`
- `humanitarian_*`
- `governance_*`
- `election_*`
- `climate_*`
- `security_*`
- `trade_*`
- `shipping_*`
- `spillover_*`

**Step 2:** Build the missing downstream-serving tables required by the prompt pack:
- `gold_entity_day_features`
- `gold_entity_day_labels`
- `gold_report_inputs`
- `gold_social_inputs`

**Step 3:** Add validation reports for each gold table and fail loudly when required feature blocks are absent.

**Step 4:** Run the end-to-end pipelines and inspect the resulting gold outputs.

Run:
- `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml`
- `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_live_country_signals.yaml`

### Task 4: Rebuild forecasting around real gold tables

**Files:**
- Modify: `src/forecasting/datasets.py`
- Modify: `src/forecasting/features.py`
- Modify: `src/forecasting/labels.py`
- Modify: `src/forecasting/train.py`
- Modify: `src/forecasting/predict.py`
- Modify: `src/forecasting/calibrate.py`
- Modify: `configs/forecasting/*`
- Modify: `docs/forecasting.md`
- Test: `src/tests/forecasting/*`

**Step 1:** Switch the default forecasting input path from synthetic fixture data to real gold tables.

**Step 2:** Make the forecast training configs point to real feature contracts, not ad hoc CSV fixture assumptions.

**Step 3:** Keep synthetic fixtures only as explicit test fixtures and demo data, not as the implied main dataset.

**Step 4:** Ensure outputs include:
- entity id / name
- forecast date
- target
- horizon
- raw score
- calibrated probability
- model version
- training window id
- top drivers
- feature snapshot hash

**Step 5:** Re-run training and prediction on real platform outputs.

Run:
- `python -m pytest src/tests/forecasting -q`
- `python -m src.forecasting.train --config configs/forecasting/train_country_day_30d.yaml`
- `python -m src.forecasting.predict --config configs/forecasting/predict_country_day.yaml`

### Task 5: Implement the missing backtesting subsystem

**Files:**
- Create: `src/backtesting/engine.py`
- Create: `src/backtesting/windows.py`
- Create: `src/backtesting/experiments.py`
- Create: `src/backtesting/evaluators.py`
- Create: `src/backtesting/alerting.py`
- Create: `src/backtesting/plots.py`
- Create: `src/backtesting/reports.py`
- Create: `src/backtesting/schemas.py`
- Create: `src/backtesting/registry.py`
- Create: `src/backtesting/cli.py`
- Create: `configs/backtesting/*`
- Create: `src/tests/backtesting/*`
- Create: `docs/backtesting.md`

**Step 1:** Implement expanding-window and rolling-window experiment definitions.

**Step 2:** Add alert logic and episode-aware evaluation:
- onset windows
- collapsed repeated alerts
- first-alert lead time
- false-alert burden

**Step 3:** Compare the main models against baseline models:
- prior-rate baseline
- lagged-events logistic baseline
- optional region-average baseline

**Step 4:** Save per-experiment outputs:
- config snapshot
- window definitions
- metrics tables
- calibration artifacts
- prediction tables
- alert tables
- plots
- markdown summary report

**Step 5:** Add replay mode for selected country/time slices.

Run:
- `python -m pytest src/tests/backtesting -q`
- `python -m src.backtesting.cli run --config configs/backtesting/country_week.yaml`
- `python -m src.backtesting.cli replay --config configs/backtesting/replay_iran.yaml`

### Task 6: Declare forecasting complete only after backtesting

**Files:**
- Modify: `docs/current_state.md`
- Modify: `README.md`
- Modify: `docs/forecasting.md`

**Step 1:** Update status documents so forecasting is marked complete only when:
- data layer Phase A is complete
- forecasting uses real gold tables
- backtesting runs from config and produces reports

**Step 2:** Add runbook commands for the end-to-end core stack.

Run:
- `python -m pytest src/tests/data_platform src/tests/forecasting src/tests/backtesting -q`

## Acceptance Rule

This plan is complete only when all three statements are true:

1. the Phase A data layer is complete for the prompt-defined MVP
2. forecasting runs on real prepared platform tables
3. backtesting exists and validates the forecasting outputs in forward time

Until then, forecasting should be described as `in progress`, not complete.
