# Backtesting

This package now contains a runnable backtesting subsystem under `src/backtesting/`.

Current implementation:

- walk-forward windows over the real `country_week_features` table
- per-model out-of-sample prediction tables
- per-fold calibration fit only on each training slice before scoring the held-out fold
- alert collapsing and false-alert burden summaries
- markdown summary reports with baseline comparisons, top-model summaries, calibration notes, and plot references
- replay mode for a selected entity timeline, with the replayed model named explicitly in the output

Run commands:

```bash
python -m src.backtesting.cli run --config configs/backtesting/country_week.yaml
python -m src.backtesting.cli run --config configs/backtesting/country_week_logit.yaml
python -m src.backtesting.cli replay --config configs/backtesting/replay_iran.yaml
```

Publish the latest website-facing backtest summary into the canonical site snapshot bundle:

```bash
python -m src.website_publishing.cli --config configs/website_publishing/site_snapshot.yaml
```

The checked-in publisher config also points at the conservative weekly baseline prediction, training, calibration, and backtest paths so the site bundle can fall back safely without claiming the wrong model provenance if the preferred live artifact is missing or malformed.

Current v1 notes:

- the current backtest config is wired to the real weekly country table
- `country_week.yaml` keeps the conservative `prior_rate` baseline
- `country_week_logit.yaml` compares the richer logistic model against the explicit `prior_rate` baseline with the weekly 120/30/30 split
- if `baseline_model` is omitted, comparisons only default to `prior_rate` when that model is actually present; otherwise the run reports no baseline comparison
- `replay_iran.yaml` can pin `model_name` explicitly instead of relying on the backtest primary model
- the backtesting package is now an implemented subsystem rather than methodology-only copy
- the website publication layer now consumes `metrics.json` from the backtest run and normalizes the top-model and alert-burden fields into a web-safe JSON bundle
