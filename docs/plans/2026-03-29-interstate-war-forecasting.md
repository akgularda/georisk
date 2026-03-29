# Interstate War Forecasting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a real interstate-war forecasting path, backed by official UCDP onset datasets and weekly onset-date localization, while preserving the broader conflict-onset system.

**Architecture:** Add official UCDP intrastate and interstate onset truth tables, localize those annual onsets to first GED event dates, rebuild weekly onset labels from the localized dates, train structural and trigger models for interstate war onset, and publish a distinct interstate watch to the website.

**Tech Stack:** Python, pandas, scikit-learn, parquet artifacts, UCDP CSV datasets, Next.js App Router

---

### Task 1: Add official UCDP onset ingestion and normalization

**Files:**
- Create: `src/data_platform/ingestion/ucdp_onset.py`
- Create: `src/data_platform/normalization/ucdp_onset.py`
- Modify: `src/data_platform/schemas.py`
- Modify: `src/data_platform/orchestration/pipeline.py`
- Test: `src/tests/data_platform/test_ucdp_onset.py`

### Task 2: Add onset dataset config to the country-week pipeline

**Files:**
- Modify: `configs/data_platform/pipeline_country_week_features.yaml`
- Modify: `configs/data_platform/source_registry.yaml`
- Modify: `src/data_platform/orchestration/pipeline.py`
- Test: `src/tests/data_platform/test_catalog.py`

### Task 3: Build official-onset localization helpers

**Files:**
- Modify: `src/data_platform/serving/country_week_features.py`
- Test: `src/tests/data_platform/test_country_week_features.py`

Implementation:
- parse interstate and intrastate `conflict_ids`
- match them to GED `conflict_new_id`
- recover localized onset dates by country-year and conflict id

### Task 4: Replace heuristic onset labels with official localized conflict-onset labels

**Files:**
- Modify: `src/data_platform/serving/country_week_features.py`
- Test: `src/tests/data_platform/test_country_week_features.py`
- Test: `src/tests/data_platform/test_country_week_features_pipeline.py`

Implementation:
- redefine `label_onset_30d` and `label_onset_90d` from official localized conflict onset dates
- add explicit alias columns `label_conflict_onset_30d` and `label_conflict_onset_90d`

### Task 5: Add explicit interstate weekly labels

**Files:**
- Modify: `src/data_platform/serving/country_week_features.py`
- Modify: `src/data_platform/serving/entity_day_labels.py`
- Test: `src/tests/data_platform/test_country_week_features.py`
- Test: `src/tests/data_platform/test_country_week_features_pipeline.py`
- Test: `src/tests/data_platform/test_catalog.py`

Implementation:
- add `label_interstate_onset_30d`
- add `label_interstate_onset_90d`
- export both into the daily label table

### Task 6: Add interstate structural and trigger forecasting configs

**Files:**
- Create: `configs/forecasting/train_country_week_interstate_onset_structural_90d.yaml`
- Create: `configs/forecasting/calibrate_country_week_interstate_onset_structural_90d.yaml`
- Create: `configs/forecasting/predict_country_week_interstate_onset_structural_90d.yaml`
- Create: `configs/forecasting/explain_country_week_interstate_onset_structural_90d.yaml`
- Create: `configs/forecasting/train_country_week_interstate_onset_logit_30d.yaml`
- Create: `configs/forecasting/calibrate_country_week_interstate_onset_logit.yaml`
- Create: `configs/forecasting/predict_country_week_interstate_onset_logit.yaml`
- Create: `configs/forecasting/explain_country_week_interstate_onset_logit.yaml`
- Test: `src/tests/forecasting/test_pipeline_integration.py`

### Task 7: Add interstate backtesting configs and replay configs

**Files:**
- Create: `configs/backtesting/country_week_interstate_onset_logit.yaml`
- Create: `configs/backtesting/country_week_interstate_onset_structural_90d.yaml`
- Create: `configs/backtesting/replay_isr.yaml`
- Create: `configs/backtesting/replay_irn_interstate.yaml`
- Test: `src/tests/backtesting/test_backtesting_integration.py`

### Task 8: Wire structural-prior support for interstate trigger training

**Files:**
- Modify: `src/forecasting/schemas.py`
- Modify: `src/forecasting/datasets.py`
- Modify: `src/tests/forecasting/test_contracts.py`
- Test: `src/tests/forecasting/test_pipeline_integration.py`

### Task 9: Add interstate provenance to website publishing

**Files:**
- Modify: `configs/website_publishing/site_snapshot.yaml`
- Modify: `src/website_publishing/schemas.py`
- Modify: `src/website_publishing/builder.py`
- Modify: `contracts/website_snapshot.schema.json`
- Test: `src/tests/website_publishing/test_builder.py`
- Test: `src/tests/website_publishing/test_schemas.py`

### Task 10: Surface interstate watch on the website

**Files:**
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/lib/live-snapshot.ts`
- Modify: `web/src/lib/site-data-core.ts`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/status/page.tsx`
- Modify: `web/src/app/methodology/page.tsx`
- Test: `web/src/lib/__tests__/site-data.test.ts`
- Test: `web/src/lib/__tests__/live-snapshot.test.ts`

### Task 11: Update report and social copy for interstate semantics

**Files:**
- Modify: `src/data_platform/serving/report_inputs.py`
- Modify: `src/data_platform/serving/social_inputs.py`
- Test: `src/tests/data_platform/test_report_inputs.py`
- Test: `src/tests/data_platform/test_social_inputs.py`

### Task 12: Extend the backend refresh automation

**Files:**
- Modify: `scripts/run_backend_refresh.ps1`

Implementation:
- run official-onset data refresh
- train interstate structural model
- train interstate trigger model
- run interstate backtests
- publish interstate provenance to the website snapshot

### Task 13: Update public methodology

**Files:**
- Modify: `web/content/methodology/model.mdx`
- Modify: `web/content/methodology/backtesting.mdx`
- Modify: `web/content/methodology/data.mdx`
- Modify: `docs/model_card_template.md`

### Task 14: Verify end to end

**Files:**
- Modify: `docs/current_state.md`
- Modify: `final.md`

Run:
- `python -m pytest src/tests/data_platform/test_ucdp_onset.py src/tests/data_platform/test_country_week_features.py src/tests/data_platform/test_country_week_features_pipeline.py src/tests/data_platform/test_catalog.py -q`
- `python -m pytest src/tests/forecasting/test_contracts.py src/tests/forecasting/test_pipeline_integration.py -q`
- `python -m pytest src/tests/backtesting/test_engine_and_reports.py src/tests/backtesting/test_backtesting_integration.py -q`
- `python -m pytest src/tests/website_publishing/test_schemas.py src/tests/website_publishing/test_builder.py -q`
- `python -m pytest src/tests/data_platform/test_report_inputs.py src/tests/data_platform/test_social_inputs.py -q`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_backend_refresh.ps1`
- `npm run test:runtime`
- `npm run content:validate`
- `npm run lint`
- `npm run build`

### Task 15: Validate the war-forecasting claim honestly

**Files:**
- Create: `docs/interstate_replay_assessment_2026-03-29.md`

Implementation:
- replay Israel and Iran in the official interstate watch artifacts
- state whether the interstate model elevated them before February 28, 2026
- distinguish held-out evidence from live full-sample replay
