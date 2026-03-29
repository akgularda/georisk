# Forecasting Model Design

## Goal

Bootstrap the forecasting layer first, using a `country_day` default with interfaces that remain compatible with future `adm1_day` support.

## Architecture

The forecasting package will consume point-in-time feature tables instead of embedding source-specific ingestion logic. It will define:
- explicit target and horizon registries
- configurable label builders
- walk-forward dataset splits
- baseline and tree-based model training
- separate calibration artifacts
- prediction and explanation outputs with stable schemas

## Initial assumptions

- Synthetic local fixture data will stand in for the future data platform.
- LightGBM is the primary tree model.
- Logistic regression and prior-rate baselines provide comparison models.
- Calibration uses isotonic regression by default.
- Tree-model explanations use contribution values from the fitted LightGBM booster.

## Risks

- Real feature availability timestamps are not yet enforced by a data layer, so the feature contract must be explicit and conservative.
- Cross-target label definitions are placeholders until real event semantics are connected.

