# Forecasting Layer

This package now implements a real weekly forecasting path for the geopolitical early-warning platform.

## What is included

- target registry with five default crisis targets
- default horizons: 7, 30, 90 days
- configurable label builders
- external label definitions in `configs/forecasting/label_definitions.yaml`
- direct training on precomputed real label columns
- walk-forward validation
- baseline models plus LightGBM
- weighted ensemble support for constituent models
- separate calibration artifacts
- prediction outputs with calibrated probabilities plus signed positive and negative drivers
- explanation artifacts derived from saved models
- skipped-fold tracking for sparse walk-forward windows
- persisted feature imputation inside the saved model artifact so predict/explain use the same fill values as training

## Project layout

- `configs/forecasting/`: training, calibration, prediction, and explanation configs
- `configs/forecasting/label_definitions.yaml`: target label registry
- `src/forecasting/`: forecasting package
- `src/tests/forecasting/`: contract and integration tests
- `data/fixtures/`: synthetic local dataset
- `data/gold/country_week_features/country_week_features.parquet`: real weekly model input
- `notebooks/forecasting_demo.py`: end-to-end demo script

## Local workflow

Train the 30-day real weekly model:

```bash
python -m src.forecasting.train --config configs/forecasting/train_country_week_30d.yaml
```

That config is the safe baseline. It keeps the `prior_rate` model path available even when early walk-forward folds only contain one class.

For a richer weekly model, use the logistic-regression or LightGBM configs:

```bash
python -m src.forecasting.train --config configs/forecasting/train_country_week_logit_30d.yaml
python -m src.forecasting.train --config configs/forecasting/train_country_week_lightgbm_30d.yaml
```

Those richer configs use the same weekly gold table, but they skip folds that do not have both classes in the training window. The skipped folds are recorded in `metrics.json` so the run stays auditable instead of crashing.

The split settings are expressed in observation periods at the dataset granularity. On `country_week` data that means weekly rows, so the preferred keys are `min_train_periods`, `validation_window_periods`, and `step_periods`. Legacy `*_days` keys are still accepted for compatibility.

Training writes combined validation predictions for every model that actually produced fold outputs. Calibration then selects rows by `model_name`, so a richer model that never generated validation predictions fails clearly instead of being silently replaced by another model.

Prediction validates that the supplied calibration run was fit for the same `model_name` and the same training run/window, and prediction artifacts now record both the scoring model and the applied calibration provenance. Explanation generation validates that provenance before reading model artifacts.

Calibrate probabilities:

```bash
python -m src.forecasting.calibrate --config configs/forecasting/calibrate_country_week.yaml --training-run-dir artifacts/forecasting/train/country_week_30d
```

For the richer logistic run, use:

```bash
python -m src.forecasting.calibrate --config configs/forecasting/calibrate_country_week_logit.yaml --training-run-dir artifacts/forecasting/train/country_week_logit_30d
```

Generate predictions:

```bash
python -m src.forecasting.predict --config configs/forecasting/predict_country_week.yaml --training-run-dir artifacts/forecasting/train/country_week_30d --calibration-run-dir artifacts/forecasting/calibration/country_week_default
```

For the richer logistic run, use:

```bash
python -m src.forecasting.predict --config configs/forecasting/predict_country_week_logit.yaml --training-run-dir artifacts/forecasting/train/country_week_logit_30d --calibration-run-dir artifacts/forecasting/calibration/country_week_logit
```

Generate explanations:

```bash
python -m src.forecasting.explain --config configs/forecasting/explain_country_week.yaml --training-run-dir artifacts/forecasting/train/country_week_30d --prediction-file artifacts/forecasting/predict/country_week_default/predictions.parquet
```

For the richer logistic run, use:

```bash
python -m src.forecasting.explain --config configs/forecasting/explain_country_week_logit.yaml --training-run-dir artifacts/forecasting/train/country_week_logit_30d --prediction-file artifacts/forecasting/predict/country_week_logit/predictions.parquet
```

Run the forecasting tests:

```bash
python -m pytest src/tests/forecasting -q
```

Publish the canonical website snapshot bundle from the latest forecasting, backtesting, and report-input artifacts:

```bash
python -m src.website_publishing.cli --config configs/website_publishing/site_snapshot.yaml
```

That publisher config names both the preferred logistic artifact lineage and the safe weekly baseline lineage:

- `artifacts/forecasting/predict/country_week_logit/predictions.parquet`
- `artifacts/forecasting/train/country_week_logit_30d/...`
- `artifacts/forecasting/calibration/country_week_logit/...`

and:

- `artifacts/forecasting/predict/country_week_default/predictions.parquet`
- `artifacts/forecasting/train/country_week_30d/...`
- `artifacts/forecasting/calibration/country_week_default/...`

If the preferred artifact is missing or invalid, publication falls back to the baseline only when that full baseline lineage has actually been generated, so the published model card and provenance stay aligned with the predictions being served.

## Current operating notes

- The real forecast path now consumes the weekly gold serving table directly.
- Synthetic fixtures remain in the repo for testing and demo-only usage.
- The current real weekly dataset is still sparse, so the default real config keeps the `prior_rate` baseline first.
- Logistic regression and LightGBM now run on the real weekly table when a fold has both classes; folds without sufficient class balance are skipped and recorded rather than failing the run.
- Missing numeric feature values are filled with a persisted constant-zero imputer inside each trained model artifact, so training, prediction, and explanation stay aligned.
- Validation predictions are stored with `model_name`, and calibration now requires the requested model to be present in that validation set.
- Prediction artifacts record `model_name`, `calibration_run_name`, `calibration_model_name`, `calibration_training_run_name`, `calibration_training_window_id`, and `calibration_method`, and explanation runs validate those provenance fields.
- Prediction and explanation steps are tolerant of skipped folds because they load the saved model artifacts that actually exist, but they now fail loudly if the requested model artifact is missing instead of silently switching models.
- Local explanation payloads use JSON strings for driver lists, matching the prediction artifact format.
- When validation folds are untrainable but the full training frame still has both classes, training now saves a final model artifact with a `final_model_only` status even though calibration remains unavailable until validation predictions exist.
- Ensemble manifests are resolved to the members that actually produced validation predictions, so the deployed ensemble matches the scored and calibrated ensemble rather than reintroducing `final_model_only` members at prediction time.
- The website publication layer now reads the saved prediction, training, and calibration artifacts through `src.website_publishing/` instead of relying on the web app to parse Parquet directly.
