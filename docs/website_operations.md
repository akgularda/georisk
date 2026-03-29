# Website Operations

## Purpose

This site is designed to keep publishing the latest available forecast snapshot without relying on manual editorial upkeep.

The operating model is:

- build a canonical website snapshot from forecasting and backtesting artifacts
- store immutable bundle directories
- update a latest-manifest pointer atomically
- let the website read the latest published snapshot rather than reconstructing state from local Parquet files

## Production Rules

The preferred long-term production model is still:

- a durable storage layer for published bundles
- an external scheduler or platform-native scheduler for publication

This repo now also supports a practical once-daily GitHub Actions publication path for the live website bundle.

Use the scheduled workflow in [.github/workflows/daily-site-refresh.yml](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/.github/workflows/daily-site-refresh.yml) when the deployment model is:

- refresh forecasting and backtesting artifacts once per day
- rebuild the live website snapshot bundle
- validate the web app against that fresh bundle
- commit only `artifacts/website_publishing/site_snapshot/latest/**` back to the repository

Do not treat GitHub Actions artifacts as the publication store. The durable published state is the committed live snapshot bundle in the repo.

## Local Bundle Layout

The local filesystem adapter writes bundles in this shape:

- `bundles/<published_at>-<snapshot_id>/manifest.json`
- `bundles/<published_at>-<snapshot_id>/forecast_snapshot.json`
- `bundles/<published_at>-<snapshot_id>/backtest_summary.json`
- `bundles/<published_at>-<snapshot_id>/model_card.json`
- `bundles/<published_at>-<snapshot_id>/status.json`
- `bundles/<published_at>-<snapshot_id>/countries/<iso3>.json`
- `latest_manifest.json`

The bundle directory is immutable once published.

The latest manifest pointer is updated atomically after the bundle lands.

## Verification Commands

Run these locally when changing publication or web consumption behavior:

- `python -m pytest src/tests/common/test_backend_refresh.py -q`
- `python -m pytest src/tests/website_publishing -q`
- `python scripts/run_backend_refresh.py --skip-revalidate`
- `npm run content:validate`
- `npm run lint`
- `npm run build`

## Daily Automation

The scheduled workflow runs once per day at `06:30` Europe/Istanbul (`03:30` UTC) and can also be started manually with `workflow_dispatch`.

Expected repository configuration:

- GitHub secret `OPENROUTER_API_KEY` if AI-written country reasons are desired
- GitHub variable `OPENROUTER_MODEL` for the model identifier
- optional GitHub variable `OPENROUTER_BASE_URL` when the default OpenRouter endpoint should be overridden

If no OpenRouter secret or model is configured, the publication path still works and falls back to deterministic rule-based summaries.

The workflow uploads refresh logs from `artifacts/ops/*.log` as run artifacts, but those logs are ignored from version control.

## Failure Handling

If the latest bundle is missing or stale, the website must show that state explicitly.

Do not silently fall back to curated content for operational ranking.
Do not hide freshness, baseline fallback, or outage conditions.
