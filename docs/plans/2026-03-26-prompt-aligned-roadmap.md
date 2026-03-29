# Prompt-Aligned Roadmap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bring the current `georisk/` repository into prompt-aligned order without losing context, by finishing the data platform first, reconnecting forecasting to real data, building backtesting, and only then resuming publication-layer expansion.

**Architecture:** The repo already contains three unequal layers: a forecasting scaffold, a partial real-source data platform, and a publishing frontend. The roadmap should stop adding surface area in the website until the missing middle layers are complete, especially the prompt-required data coverage and the fully separate backtesting subsystem. Forecasting is not considered complete until it is trained on real platform tables and evaluated in backtests.

**Tech Stack:** Python, Pandas, Pytest, YAML configs, Next.js App Router, TypeScript, MDX, GitHub Actions

---

### Task 1: Finish the prompt-required data-platform baseline

**Files:**
- Modify: `src/data_platform/ingestion/*`
- Modify: `src/data_platform/normalization/*`
- Modify: `src/data_platform/serving/country_week_features.py`
- Modify: `configs/data_platform/*`
- Modify: `docs/data_platform.md`
- Test: `src/tests/data_platform/*`

**Step 1:** Add the missing source-priority registry and document which catalog sources are `implemented`, `stubbed`, and `missing`.

**Step 2:** Implement the next mandatory open or account-based sources in the catalog order, starting with `ACLED`, then the missing macro / governance / election / food / climate layers that can realistically feed `country_week_features`.

**Step 3:** Expand `country_week_features` so its feature families match the catalog contracts:
- `gdelt_*`
- `acled_*`
- `ucdp_history_*`
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

**Step 4:** Run the data-platform tests and pipeline commands again.

Run:
- `python -m pytest src/tests/data_platform -q`
- `python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml`

### Task 2: Reconnect forecasting to real feature tables

**Files:**
- Modify: `src/forecasting/datasets.py`
- Modify: `src/forecasting/train.py`
- Modify: `src/forecasting/predict.py`
- Modify: `src/forecasting/labels.py`
- Modify: `configs/forecasting/*`
- Modify: `docs/forecasting.md`
- Test: `src/tests/forecasting/*`

**Step 1:** Replace the synthetic-first training path with a real-table-first training path built on the gold platform outputs.

**Step 2:** Make label generation and feature loading explicitly point-in-time with the real data contracts.

**Step 3:** Keep synthetic fixtures only as development fixtures, not as the implied main data path.

**Step 4:** Re-run the forecasting tests and CLI training commands.

Run:
- `python -m pytest src/tests/forecasting -q`
- `python -m src.forecasting.train --config configs/forecasting/train_country_day_30d.yaml`

**Exit condition for Task 2:**
- a real-data forecast pipeline exists
- but forecasting is still not treated as complete until Task 3 is done

### Task 3: Build the missing backtesting subsystem

**Files:**
- Create: `src/backtesting/*`
- Create: `configs/backtesting/*`
- Create: `src/tests/backtesting/*`
- Create: `docs/backtesting.md`
- Modify: `README.md`

**Step 1:** Implement a standalone backtesting package instead of burying evaluation inside training outputs.

**Step 2:** Add rolling or expanding forward-time evaluation, onset logic, threshold analysis, baseline comparison, and artifact outputs required by `04_backtesting.md`.

**Step 3:** Generate a first reproducible historical replay artifact from the real platform tables.

**Step 4:** Add backtesting tests and CLI verification.

Run:
- `python -m pytest src/tests/backtesting -q`
- `python -m src.backtesting.cli --config configs/backtesting/<config>.yaml`

### Task 4: Rewire the website to real platform and model artifacts

**Files:**
- Modify: `web/src/lib/site-data.ts`
- Modify: `web/src/lib/content.ts`
- Modify: `web/src/app/forecasts/page.tsx`
- Modify: `web/src/app/countries/[slug]/page.tsx`
- Modify: `web/src/app/reports/[slug]/page.tsx`
- Modify: `web/content/*`
- Modify: `web/README.md`

**Step 1:** Stop treating the website as primarily sample-data-driven once forecast and backtest artifacts exist.

**Step 2:** Feed the forecast explorer and country pages from stored artifacts and gold tables.

**Step 3:** Keep `design.md` as the design constraint, but let the artifacts drive the content and timestamps.

**Step 4:** Re-run content validation, lint, build, and browser checks.

Run:
- `npm run content:validate`
- `npm run lint`
- `npm run build`

### Task 5: Implement the social publishing subsystem last

**Files:**
- Create: `src/social_publishing/*`
- Create: `configs/social/*`
- Create: `src/tests/social_publishing/*`
- Create: `docs/social_publishing.md`

**Step 1:** Implement draft generation, review modes, guardrails, and publishing contracts only after forecasts and reports are grounded in real artifacts.

**Step 2:** Add scheduling, audit logs, and analytics capture required by `03_social_media_publishing.md`.

**Step 3:** Verify that the social layer consumes forecast/report outputs instead of inventing its own logic.

## Decision Rule

Until `Task 3` is complete, do not expand the website beyond maintenance and data-wiring work.
Backtesting is the missing subsystem that currently breaks the intended project order.

Practical sequence:
1. complete data layer
2. real-data forecasting
3. backtesting
4. only then resume major website/design work
