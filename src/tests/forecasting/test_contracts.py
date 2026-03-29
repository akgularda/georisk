from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.forecasting.datasets import build_walk_forward_splits
from src.forecasting.horizons import DEFAULT_HORIZONS_DAYS
from src.forecasting.schemas import DatasetSpec, PredictionConfig, SplitConfig, TrainingConfig, UnitOfAnalysis
from src.forecasting.targets import DEFAULT_TARGETS


def test_default_forecast_contracts_are_exposed() -> None:
    assert DEFAULT_HORIZONS_DAYS == (7, 30, 90)
    assert UnitOfAnalysis.COUNTRY_DAY.value == "country_day"
    assert UnitOfAnalysis.COUNTRY_WEEK.value == "country_week"
    assert "organized_violence_onset" in DEFAULT_TARGETS


def test_walk_forward_splits_are_strictly_time_ordered() -> None:
    frame = pd.DataFrame(
        {
            "as_of_date": [date(2024, 1, 1) + timedelta(days=offset) for offset in range(80)],
            "entity_id": ["usa"] * 80,
            "feature_a": list(range(80)),
        }
    )
    spec = DatasetSpec(
        entity_id_column="entity_id",
        entity_name_column="entity_id",
        date_column="as_of_date",
        unit_of_analysis=UnitOfAnalysis.COUNTRY_DAY,
        feature_columns=["feature_a"],
    )

    splits = build_walk_forward_splits(
        frame=frame,
        dataset_spec=spec,
        min_train_periods=30,
        validation_window_periods=10,
        step_periods=10,
    )

    assert splits
    for split in splits:
        assert split.train_end < split.validation_start
        assert split.validation_end >= split.validation_start


def test_split_config_accepts_legacy_day_aliases() -> None:
    split_config = SplitConfig.model_validate(
        {
            "min_train_days": 14,
            "validation_window_days": 7,
            "step_days": 7,
            "max_splits": 3,
        }
    )

    assert split_config.min_train_periods == 14
    assert split_config.validation_window_periods == 7
    assert split_config.step_periods == 7


def test_walk_forward_splits_use_observation_periods_for_weekly_data() -> None:
    frame = pd.DataFrame(
        {
            "week_start_date": [date(2024, 1, 1) + timedelta(days=7 * offset) for offset in range(24)],
            "entity_id": ["usa"] * 24,
            "feature_a": list(range(24)),
        }
    )
    spec = DatasetSpec(
        entity_id_column="entity_id",
        entity_name_column="entity_id",
        date_column="week_start_date",
        unit_of_analysis=UnitOfAnalysis.COUNTRY_WEEK,
        feature_columns=["feature_a"],
    )

    splits = build_walk_forward_splits(
        frame=frame,
        dataset_spec=spec,
        min_train_periods=12,
        validation_window_periods=4,
        step_periods=4,
        max_splits=1,
    )

    assert len(splits) == 1
    split = splits[0]
    train_dates = frame.loc[frame["week_start_date"].between(split.train_start, split.train_end), "week_start_date"].tolist()
    validation_dates = frame.loc[
        frame["week_start_date"].between(split.validation_start, split.validation_end),
        "week_start_date",
    ].tolist()

    assert len(train_dates) == 12
    assert len(validation_dates) == 4


def test_training_and_prediction_configs_accept_optional_structural_prior() -> None:
    training_config = TrainingConfig.model_validate(
        {
            "run_name": "country_week_onset_trigger",
            "dataset_path": "data/gold/country_week_features/country_week_features.parquet",
            "dataset_spec": {
                "entity_id_column": "country_iso3",
                "entity_name_column": "country_iso3",
                "date_column": "week_start_date",
                "unit_of_analysis": "country_week",
                "feature_columns": ["feature_a"],
            },
            "target_name": "country_week_onset_30d",
            "horizon_days": 30,
            "label_column": "label_onset_30d",
            "models": [{"name": "logit", "kind": "logistic_regression"}],
            "primary_model": "logit",
            "structural_prior": {
                "prediction_file": "artifacts/forecasting/predict/country_week_onset_structural_90d/predictions.parquet",
                "feature_name": "structural_prior_score",
            },
        }
    )
    prediction_config = PredictionConfig.model_validate(
        {
            "run_name": "country_week_onset_trigger",
            "dataset_path": "data/gold/country_week_features/country_week_features.parquet",
            "dataset_spec": {
                "entity_id_column": "country_iso3",
                "entity_name_column": "country_iso3",
                "date_column": "week_start_date",
                "unit_of_analysis": "country_week",
                "feature_columns": ["feature_a"],
            },
            "model_name": "logit",
            "structural_prior": {
                "prediction_file": "artifacts/forecasting/predict/country_week_onset_structural_90d/predictions.parquet",
                "feature_name": "structural_prior_score",
            },
        }
    )

    assert training_config.structural_prior is not None
    assert prediction_config.structural_prior is not None
    assert training_config.structural_prior.feature_name == "structural_prior_score"
    assert prediction_config.structural_prior.score_column == "calibrated_probability"
