# Current State

Snapshot date: `2026-03-29`

This file is the short factual status map for the implementation repo in `georisk/`.

## Direct Answer

- Data platform: live and dense at the weekly country level, with downstream gold exports.
- Forecasting: onset-first, with a live two-layer path.
- Backtesting: live for baseline, onset trigger, escalation, and structural onset prior.
- Website publishing: live, snapshot-backed, and now publishes structural provenance.
- Website UI: live runtime/status surfaces show structural-prior status and health.
- Social publishing: still dry-run only.

## Live Release State

- Primary public target: `onset`
- Public alert state: `No Clear Leader`
- Public model status: `monitoring_only`
- Current lead country in the published snapshot: `Australia`
- Coverage count: `30`
- Lead tie count: `16`

The website is intentionally abstaining. The system is live, but it is not claiming a sharp winner where the ranking is weak.

## What Is Now Built

- Real weekly gold table:
  - `data/gold/country_week_features/country_week_features.parquet`
- Real day-label export with horizons `7`, `30`, and `90`:
  - `data/gold/entity_day_labels/entity_day_labels.parquet`
- Monitoring-grade report/social gold outputs:
  - `data/gold/report_inputs/report_inputs.parquet`
  - `data/gold/social_inputs/social_inputs.parquet`
- Structural 90-day onset prior artifacts:
  - `artifacts/forecasting/train/country_week_onset_structural_90d/`
  - `artifacts/forecasting/calibration/country_week_onset_structural_90d/`
  - `artifacts/forecasting/predict/country_week_onset_structural_90d/predictions.parquet`
  - `artifacts/backtesting/run/country_week_onset_structural_90d/`
- Trigger-model artifacts wired to the structural prior:
  - `artifacts/forecasting/train/country_week_onset_logit_30d/manifest.json`
- Published website snapshot with onset, escalation, and structural provenance:
  - `artifacts/website_publishing/site_snapshot/latest/manifest.json`
  - `artifacts/website_publishing/site_snapshot/latest/model_card.json`
  - `artifacts/website_publishing/site_snapshot/latest/status.json`

## Methodology State

- The public framing is onset-first.
- The live stack now uses a slower `90d` structural onset prior plus a faster `30d` onset trigger.
- The homepage and `/status` expose that structural layer directly.
- The publication rule still keeps the site in `No Clear Leader` / `monitoring_only` because the richer trigger model does not beat the baseline on the current promotion metrics.

## Latest Evidence

Latest successful refresh:

- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_backend_refresh.ps1`
- Log:
  - `artifacts/ops/backend-refresh-20260329-033416.log`

Latest published snapshot facts from the refresh:

- `snapshot_id: site_snapshot-2026-03-29`
- `primary_target: onset`
- `alert_type: No Clear Leader`
- `model_status: monitoring_only`
- `lead_country_name: Australia`
- `structural provenance present: yes`

Latest verified commands in this state:

- `python -m pytest src/tests/backtesting/test_backtesting_integration.py::test_checked_in_structural_backtest_config_runs_on_real_country_week_pipeline -q`
- `python -m src.backtesting.cli run --config configs/backtesting/country_week_onset_structural_90d.yaml`
- `python -m pytest src/tests/website_publishing/test_schemas.py src/tests/website_publishing/test_builder.py -q`
- `python -m pytest src/tests/data_platform/test_report_inputs.py src/tests/data_platform/test_social_inputs.py -q`
- `npm run test:runtime`
- `npm run content:validate`
- `npm run lint`
- `npm run build`
- `Invoke-RestMethod -Method Get -Uri http://localhost:3000/api/health`

## Residual Risks

- The baseline `prior_rate` still wins PR AUC in both the live onset 30-day backtest and the structural 90-day backtest.
- The public ranking is still diffuse enough to produce `No Clear Leader`.
- The site is operational and honest, but it is not yet empirically strong enough to claim mature predictive performance.
- The Next.js build still emits the known non-blocking Turbopack NFT warning tied to filesystem-backed snapshot loading in `web/src/lib/live-snapshot.ts`.

## What Not To Pretend

- This is not a proven conflict oracle.
- This is not live social posting.
- This is not a promoted alerting model.
- It is a working onset-first warning system with structural-prior wiring, explicit abstention, and verified publication provenance.
