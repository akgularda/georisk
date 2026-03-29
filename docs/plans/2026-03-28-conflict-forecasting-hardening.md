# Conflict Before It Happens Forecasting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Shift GeoRisk from a generic weekly risk board to an onset-first early-warning system that can surface the next country likely to enter organized violence before the conflict is obvious.

**Architecture:** Add a primary onset forecast path alongside the existing escalation path, strengthen the weekly feature table with trigger-oriented signals, replace the fixed threshold with backtest-selected operating thresholds, and publish machine-backed `Onset Watch`, `Escalation Watch`, and `No Clear Leader` states. Only promote a model to the homepage if it beats the baseline on rare-event operating metrics.

**Tech Stack:** Python, pandas, scikit-learn, parquet artifacts, markdown methodology pages, Next.js App Router

---

### Task 1: Make onset the primary operational target

**Files:**
- Modify: `configs/forecasting/train_country_week_logit_30d.yaml`
- Create: `configs/forecasting/train_country_week_onset_logit_30d.yaml`
- Create: `configs/forecasting/calibrate_country_week_onset_logit.yaml`
- Create: `configs/forecasting/predict_country_week_onset_logit.yaml`
- Create: `configs/forecasting/explain_country_week_onset_logit.yaml`
- Create: `configs/backtesting/country_week_onset_logit.yaml`
- Test: `src/tests/forecasting/test_pipeline_integration.py`
- Test: `src/tests/backtesting/test_backtesting_integration.py`

**Step 1: Write the failing tests**

Add integration tests that expect a valid onset training, calibration, prediction, and backtest path using `label_onset_30d`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py src/tests/backtesting/test_backtesting_integration.py -q`

Expected: failure because the onset configs do not exist yet.

**Step 3: Write minimal implementation**

Create the onset configs by cloning the working weekly config shape and changing:

- `run_name`
- `target_name`
- `label_column: label_onset_30d`
- output directories and backtest references

Keep:

- `prior_rate` baseline
- `logit` richer model
- the same country-week dataset and split policy for the first pass

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/forecasting/test_pipeline_integration.py src/tests/backtesting/test_backtesting_integration.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add configs/forecasting configs/backtesting src/tests/forecasting/test_pipeline_integration.py src/tests/backtesting/test_backtesting_integration.py
git commit -m "feat: add onset-first weekly forecasting configs"
```

### Task 2: Strengthen the weekly feature table for early warning

**Files:**
- Modify: `src/data_platform/serving/country_week_features.py`
- Modify: `src/data_platform/countries.py`
- Modify: `src/data_platform/serving/panel.py`
- Test: `src/tests/data_platform/test_country_week_features.py`
- Test: `src/tests/data_platform/test_country_week_features_pipeline.py`

**Step 1: Write the failing tests**

Add tests for these new columns:

- short-vs-medium acceleration for events and fatalities
- quiet-window flags for onset logic
- neighbor spillover features
- novelty flags for recent actor/activity emergence

Use explicit column assertions such as:

```python
assert "acled_event_count_7d_vs_28d_ratio" in result.columns
assert "acled_fatalities_7d_delta" in result.columns
assert "organized_violence_quiet_56d" in result.columns
assert "neighbor_event_count_7d" in result.columns
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/data_platform/test_country_week_features.py src/tests/data_platform/test_country_week_features_pipeline.py -q`

Expected: fail on missing columns.

**Step 3: Write minimal implementation**

Add feature generation that prefers:

- rate-of-change
- acceleration
- novelty
- spillover

Avoid adding a large feature explosion. Keep only columns that directly support onset and escalation detection.

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/data_platform/test_country_week_features.py src/tests/data_platform/test_country_week_features_pipeline.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add src/data_platform/serving/country_week_features.py src/data_platform/countries.py src/data_platform/serving/panel.py src/tests/data_platform/test_country_week_features.py src/tests/data_platform/test_country_week_features_pipeline.py
git commit -m "feat: add onset trigger features to country-week table"
```

### Task 3: Replace the fixed threshold with backtest-selected operating thresholds

**Files:**
- Modify: `src/forecasting/metrics.py`
- Modify: `src/backtesting/evaluators.py`
- Modify: `src/backtesting/alerting.py`
- Modify: `src/backtesting/reports.py`
- Modify: `src/backtesting/schemas.py`
- Test: `src/tests/backtesting/test_engine_and_reports.py`

**Step 1: Write the failing tests**

Add tests that require the backtest outputs to include:

- `publish_threshold`
- `alert_threshold`
- `recall_at_5`
- `recall_at_10`
- `episode_recall`
- `median_lead_days`
- `false_alerts_per_true_alert`

Add a test for a weak ranking where the engine emits `no_clear_leader = true`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/backtesting/test_engine_and_reports.py -q`

Expected: fail on missing fields and missing abstention behavior.

**Step 3: Write minimal implementation**

Compute candidate thresholds from the out-of-sample scores, then select the operating threshold that best balances:

- episode recall
- top-k recall
- false-alert burden

Persist the chosen thresholds and the abstention decision in the backtest outputs.

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/backtesting/test_engine_and_reports.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add src/forecasting/metrics.py src/backtesting/evaluators.py src/backtesting/alerting.py src/backtesting/reports.py src/backtesting/schemas.py src/tests/backtesting/test_engine_and_reports.py
git commit -m "feat: add operating thresholds and abstention metrics"
```

### Task 4: Publish onset-first status and no-clear-leader semantics

**Files:**
- Modify: `configs/website_publishing/site_snapshot.yaml`
- Modify: `src/website_publishing/builder.py`
- Modify: `src/website_publishing/schemas.py`
- Test: `src/tests/website_publishing/test_builder.py`
- Test: `src/tests/website_publishing/test_schemas.py`

**Step 1: Write the failing tests**

Add tests that require the published website bundle to include:

- `primary_target`
- `alert_type`
- `no_clear_leader`
- onset and escalation model provenance
- operating thresholds and top-k metrics

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/website_publishing/test_builder.py src/tests/website_publishing/test_schemas.py -q`

Expected: fail on missing snapshot fields.

**Step 3: Write minimal implementation**

Make the publisher read the onset artifacts first, then the escalation artifacts as secondary context. When the onset model does not clear the publication rule, publish either:

- `Escalation Watch`
- `Monitoring Only`
- `No Clear Leader`

Do not silently force a lead country.

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/website_publishing/test_builder.py src/tests/website_publishing/test_schemas.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add configs/website_publishing/site_snapshot.yaml src/website_publishing/builder.py src/website_publishing/schemas.py src/tests/website_publishing/test_builder.py src/tests/website_publishing/test_schemas.py
git commit -m "feat: publish onset-first alert contract"
```

### Task 5: Make the website show the right operational semantics

**Files:**
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/lib/site-data-core.ts`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/status/page.tsx`
- Modify: `web/src/app/methodology/page.tsx`

**Step 1: Write the failing tests**

Add or extend runtime tests so the site data layer can ingest:

- `Onset Watch`
- `Escalation Watch`
- `Monitoring Only`
- `No Clear Leader`

If no web tests exist for these surfaces, add a minimal parser/unit test around `site-data-core.ts`.

**Step 2: Run test to verify it fails**

Run: `npm run test:runtime`

Expected: fail because the new fields are not mapped into the web types yet.

**Step 3: Write minimal implementation**

Update the homepage and status page so the lead block explains:

- what target is being forecast
- whether the alert is onset or escalation
- whether the system abstained
- the current episode-recall and alert-burden metrics

When `no_clear_leader` is true, suppress theatrical urgency and show the monitoring state plainly.

**Step 4: Run test to verify it passes**

Run: `npm run test:runtime`

Expected: pass.

**Step 5: Commit**

```bash
git add web/src/lib/types.ts web/src/lib/site-data-core.ts web/src/app/page.tsx web/src/app/status/page.tsx web/src/app/methodology/page.tsx
git commit -m "feat: show onset-first alert states on the website"
```

### Task 6: Update the public methodology and model card

**Files:**
- Modify: `web/content/methodology/backtesting.mdx`
- Modify: `web/content/methodology/model.mdx`
- Modify: `web/content/methodology/data.mdx`
- Modify: `docs/model_card_template.md`

**Step 1: Write the failing documentation checklist**

Create a short checklist in the work session and verify the pages currently miss:

- onset-vs-escalation distinction
- threshold policy
- abstention policy
- top-k and episode metrics
- current baseline comparison

**Step 2: Run the existing content validation**

Run: `npm run content:validate`

Expected: pass before changes, but the checklist should show missing methodological content.

**Step 3: Write minimal implementation**

Update the methodology pages so they state:

- the primary target is onset-first early warning
- escalation is secondary
- thresholds come from backtests, not from a fixed `0.5`
- the site can abstain with `No Clear Leader`
- model promotion requires beating the baseline on rare-event metrics

Update the model card template so it includes:

- recall@5
- recall@10
- episode recall
- median lead days
- false alerts per true alert
- no-clear-leader rate

**Step 4: Run content validation**

Run: `npm run content:validate`

Expected: pass.

**Step 5: Commit**

```bash
git add web/content/methodology/backtesting.mdx web/content/methodology/model.mdx web/content/methodology/data.mdx docs/model_card_template.md
git commit -m "docs: align public methodology with onset-first forecasting"
```

### Task 7: Add the structural prior as the next-stage research upgrade

**Files:**
- Create: `configs/forecasting/train_country_week_onset_structural_90d.yaml`
- Modify: `src/forecasting/train.py`
- Modify: `src/forecasting/predict.py`
- Modify: `src/forecasting/schemas.py`
- Test: `src/tests/forecasting/test_contracts.py`
- Test: `src/tests/forecasting/test_pipeline_integration.py`

**Step 1: Write the failing tests**

Add a test for an optional prior-score input path so a weekly onset trigger model can consume a slower structural prior score without breaking the current single-stage configs.

**Step 2: Run test to verify it fails**

Run: `python -m pytest src/tests/forecasting/test_contracts.py src/tests/forecasting/test_pipeline_integration.py -q`

Expected: fail because the schema and train/predict path do not support the prior score contract yet.

**Step 3: Write minimal implementation**

Add optional config/schema support for:

- a structural prior prediction artifact
- joining that prior score into the weekly training and prediction frame

Keep this strictly optional so the current configs continue to work.

**Step 4: Run test to verify it passes**

Run: `python -m pytest src/tests/forecasting/test_contracts.py src/tests/forecasting/test_pipeline_integration.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add configs/forecasting/train_country_week_onset_structural_90d.yaml src/forecasting/train.py src/forecasting/predict.py src/forecasting/schemas.py src/tests/forecasting/test_contracts.py src/tests/forecasting/test_pipeline_integration.py
git commit -m "feat: support structural prior inputs for onset models"
```

### Task 8: Full verification and promotion gate

**Files:**
- Verify: `artifacts/forecasting/train/*`
- Verify: `artifacts/backtesting/run/*`
- Verify: `artifacts/website_publishing/site_snapshot/latest/*`

**Step 1: Run forecasting and backtesting tests**

Run: `python -m pytest src/tests/forecasting src/tests/backtesting src/tests/website_publishing -q`

Expected: pass.

**Step 2: Run data-platform tests**

Run: `python -m pytest src/tests/data_platform -q`

Expected: pass.

**Step 3: Run the end-to-end backend refresh**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_backend_refresh.ps1`

Expected: success with fresh onset, escalation, backtest, and website snapshot artifacts.

**Step 4: Run web verification**

Run:

```bash
npm run test:runtime
npm run content:validate
npm run lint
npm run build
```

Expected: all pass.

**Step 5: Promotion decision**

Promote the onset model to the homepage only if the fresh backtest shows:

- PR AUC >= baseline
- recall@10 > baseline
- episode recall > baseline
- median lead days > 0
- acceptable false-alert burden

If those conditions fail, leave the site in `Monitoring Only` or `No Clear Leader` mode and do not claim predictive maturity.
