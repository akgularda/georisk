# AGENTS.md

## Mission

This repository builds a geopolitical early-warning platform that ingests historical and live data, forecasts crisis risk, backtests those forecasts in forward time, and publishes explainable outputs.

The system must behave like a disciplined analyst platform, not a hype machine.

## Core rules

1. Inspect the relevant code and configs before editing.
2. Prefer incremental implementation and targeted validation.
3. Preserve subsystem boundaries between data, forecasting, backtesting, and publishing.
4. Never allow hindsight leakage across `event_date`, `published_at`, `ingested_at`, or `available_at`.
5. Forecast probabilities, not certainties.

## Forecasting defaults

- Default unit of analysis: `country_day`
- Supported horizons: `7`, `30`, `90`
- Supported targets:
  - `organized_violence_onset`
  - `organized_violence_escalation`
  - `major_unrest_escalation`
  - `interstate_confrontation_risk`
  - `humanitarian_deterioration_risk`

