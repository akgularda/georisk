from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml
import pytest

from src.data_platform.orchestration.pipeline import run_country_week_features_pipeline
from src.forecasting.calibrate import run_calibration
from src.forecasting.explain import run_explanations
from src.forecasting.metrics import compute_classification_metrics
from src.forecasting.predict import run_prediction
from src.forecasting.train import run_training


def _country_week_dataset_spec() -> dict[str, object]:
    return {
        "entity_id_column": "country_iso3",
        "entity_name_column": "country_iso3",
        "date_column": "week_start_date",
        "unit_of_analysis": "country_week",
        "group_columns": [],
        "feature_columns": [
            "gdelt_event_count_7d",
            "gdelt_avg_goldstein_7d",
            "gdelt_avg_event_tone_7d",
            "gdelt_num_mentions_7d",
            "gdelt_num_articles_7d",
            "gdelt_document_count_7d",
            "gdelt_avg_document_tone_7d",
            "acled_event_count_7d",
            "acled_fatalities_sum_7d",
            "acled_protest_count_7d",
            "acled_riot_count_7d",
            "acled_violence_against_civilians_count_7d",
            "acled_explosions_remote_violence_count_7d",
            "acled_strategic_developments_count_7d",
            "acled_distinct_actor1_count_7d",
            "acled_distinct_actor2_count_7d",
            "acled_event_count_28d",
            "acled_fatalities_sum_28d",
            "market_oil_price_usd_per_barrel",
            "market_gas_price_index",
            "market_fertilizer_price_index",
            "market_commodity_price_index",
            "food_price_index",
            "food_cereal_price_index",
            "trade_exports_value_usd",
            "trade_imports_value_usd",
            "trade_exports_3m_change_pct",
            "trade_imports_3m_change_pct",
            "shipping_lsci_index",
            "shipping_port_connectivity_index",
            "governance_voice_and_accountability",
            "governance_political_stability",
            "governance_government_effectiveness",
            "governance_regulatory_quality",
            "governance_rule_of_law",
            "governance_control_of_corruption",
            "governance_score",
            "days_to_next_election",
            "days_since_last_election",
            "election_upcoming_30d",
            "election_upcoming_90d",
            "election_recent_30d",
            "election_recent_90d",
            "climate_drought_severity_index",
            "climate_temperature_anomaly_c",
            "climate_precipitation_anomaly_pct",
            "climate_night_lights_anomaly_pct",
            "climate_night_lights_zscore",
            "security_military_expenditure_usd",
            "security_military_expenditure_pct_gdp",
            "security_arms_import_volume_index",
            "ucdp_history_event_count_52w",
            "ucdp_history_best_deaths_52w",
            "ucdp_history_state_based_events_52w",
            "macro_gdp_growth_annual_pct",
            "macro_cpi_yoy",
            "macro_population_total",
            "humanitarian_refugees",
            "humanitarian_asylum_seekers",
            "humanitarian_idps",
        ],
    }


def _write_config(path: Path, payload: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_structural_prior_predictions(
    dataset_path: Path,
    output_path: Path,
    *,
    entity_id_column: str,
    date_column: str,
    label_column: str,
) -> None:
    dataset_frame = pd.read_parquet(dataset_path)
    prior_frame = pd.DataFrame(
        {
            "entity_id": dataset_frame[entity_id_column],
            "forecast_date": dataset_frame[date_column],
            "calibrated_probability": dataset_frame[label_column].fillna(0).astype(float).map(lambda value: 0.9 if value >= 1 else 0.1),
        }
    )
    prior_frame.to_parquet(output_path, index=False)


def _write_augmented_interstate_dataset(source_path: Path, output_path: Path) -> Path:
    frame = pd.read_parquet(source_path).copy()
    frame["week_start_date"] = pd.to_datetime(frame["week_start_date"])
    frame["label_interstate_onset_30d"] = frame["label_interstate_onset_30d"].fillna(0).astype(int)
    frame["label_interstate_onset_90d"] = frame["label_interstate_onset_90d"].fillna(0).astype(int)
    frame["label_interstate_30d"] = frame["label_interstate_30d"].fillna(0).astype(int)

    selected_week_positions = [60, 120, 180, 240, 300, 360, 420, 480]
    unique_weeks = sorted(frame["week_start_date"].drop_duplicates().tolist())
    selected_weeks = {unique_weeks[index] for index in selected_week_positions if index < len(unique_weeks)}
    positive_mask = frame["country_iso3"].isin(["IRN", "ISR"]) & frame["week_start_date"].isin(selected_weeks)

    frame.loc[positive_mask, "label_interstate_onset_30d"] = 1
    frame.loc[positive_mask, "label_interstate_onset_90d"] = 1
    frame.loc[positive_mask, "label_interstate_30d"] = 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)
    return output_path


@pytest.fixture(scope="module")
def country_week_dataset_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    output_root = tmp_path_factory.mktemp("forecasting-country-week")
    data_pipeline_result = run_country_week_features_pipeline(
        project_root / "configs" / "data_platform" / "pipeline_country_week_features.yaml",
        output_root=output_root,
        use_test_snapshots=True,
    )
    return data_pipeline_result.gold_country_week_features_file


def test_training_calibration_prediction_and_explanation_pipeline(
    tmp_path: Path,
    country_week_dataset_path: Path,
) -> None:
    dataset_path = country_week_dataset_path

    train_config_path = tmp_path / "train_country_week_30d.yaml"
    calibrate_config_path = tmp_path / "calibrate_country_week.yaml"
    predict_config_path = tmp_path / "predict_country_week.yaml"
    explain_config_path = tmp_path / "explain_country_week.yaml"

    dataset_spec = _country_week_dataset_spec()

    _write_config(
        train_config_path,
        {
            "run_name": "country_week_30d",
            "dataset_path": str(dataset_path),
            "dataset_spec": dataset_spec,
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "label_column": "label_escalation_30d",
            "primary_model": "prior_rate",
            "prediction_threshold": 0.5,
            "seed": 7,
            "split": {
                "min_train_periods": 1,
                "validation_window_periods": 1,
                "step_periods": 1,
                "max_splits": 6,
            },
            "models": [{"name": "prior_rate", "kind": "prior_rate"}],
        },
    )
    _write_config(
        calibrate_config_path,
        {
            "run_name": "country_week_default",
            "model_name": "prior_rate",
            "method": "isotonic",
            "score_column": "raw_score",
            "label_column": "label",
        },
    )
    _write_config(
        predict_config_path,
        {
            "run_name": "country_week_default",
            "dataset_path": str(dataset_path),
            "model_name": "prior_rate",
            "top_n_drivers": 5,
            "prediction_output_name": "predictions.parquet",
            "dataset_spec": dataset_spec,
        },
    )
    _write_config(
        explain_config_path,
        {
            "run_name": "country_week_default",
            "model_name": "prior_rate",
            "top_n_drivers": 5,
        },
    )

    train_result = run_training(train_config_path, output_root=tmp_path)
    calibration_result = run_calibration(
        calibrate_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    prediction_result = run_prediction(
        predict_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=calibration_result.run_dir,
    )
    explanation_result = run_explanations(
        explain_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        prediction_file=prediction_result.prediction_file,
    )

    assert train_result.metrics_file.exists()
    assert calibration_result.calibrator_file.exists()
    assert prediction_result.prediction_file.exists()
    assert explanation_result.global_explanations_file.exists()

    metrics_payload = json.loads(train_result.metrics_file.read_text(encoding="utf-8"))
    assert "prior_rate" in metrics_payload["models"]

    prediction_frame = pd.read_parquet(prediction_result.prediction_file)
    assert "entity_id" in prediction_frame.columns
    assert "entity_name" in prediction_frame.columns
    assert "forecast_date" in prediction_frame.columns
    assert "model_name" in prediction_frame.columns
    assert "calibration_run_name" in prediction_frame.columns
    assert "calibration_training_run_name" in prediction_frame.columns
    assert "top_positive_drivers" in prediction_frame.columns
    assert "top_negative_drivers" in prediction_frame.columns

    local_explanations_frame = pd.read_parquet(explanation_result.local_explanations_file)
    assert isinstance(json.loads(local_explanations_frame.loc[0, "top_positive_drivers"]), list)
    assert isinstance(json.loads(local_explanations_frame.loc[0, "top_negative_drivers"]), list)


def test_checked_in_onset_weekly_configs_support_end_to_end_pipeline(
    tmp_path: Path,
    country_week_dataset_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[3]
    train_source = project_root / "configs" / "forecasting" / "train_country_week_onset_logit_30d.yaml"
    calibrate_source = project_root / "configs" / "forecasting" / "calibrate_country_week_onset_logit.yaml"
    predict_source = project_root / "configs" / "forecasting" / "predict_country_week_onset_logit.yaml"
    explain_source = project_root / "configs" / "forecasting" / "explain_country_week_onset_logit.yaml"

    train_payload = yaml.safe_load(train_source.read_text(encoding="utf-8"))
    calibrate_payload = yaml.safe_load(calibrate_source.read_text(encoding="utf-8"))
    predict_payload = yaml.safe_load(predict_source.read_text(encoding="utf-8"))
    explain_payload = yaml.safe_load(explain_source.read_text(encoding="utf-8"))

    assert train_payload["label_column"] == "label_onset_30d"
    assert train_payload["primary_model"] == "logit"
    assert calibrate_payload["model_name"] == "logit"
    assert predict_payload["model_name"] == "logit"
    assert explain_payload["model_name"] == "logit"

    train_payload["dataset_path"] = str(country_week_dataset_path)
    predict_payload["dataset_path"] = str(country_week_dataset_path)
    if "structural_prior" in train_payload or "structural_prior" in predict_payload:
        structural_prior_file = tmp_path / "country_week_onset_structural_prior.parquet"
        _write_structural_prior_predictions(
            country_week_dataset_path,
            structural_prior_file,
            entity_id_column="country_iso3",
            date_column="week_start_date",
            label_column="label_onset_90d",
        )
        if "structural_prior" in train_payload:
            train_payload["structural_prior"]["prediction_file"] = str(structural_prior_file)
        if "structural_prior" in predict_payload:
            predict_payload["structural_prior"]["prediction_file"] = str(structural_prior_file)

    train_config_path = tmp_path / "train_country_week_onset_logit_30d.yaml"
    calibrate_config_path = tmp_path / "calibrate_country_week_onset_logit.yaml"
    predict_config_path = tmp_path / "predict_country_week_onset_logit.yaml"
    explain_config_path = tmp_path / "explain_country_week_onset_logit.yaml"

    _write_config(train_config_path, train_payload)
    _write_config(calibrate_config_path, calibrate_payload)
    _write_config(predict_config_path, predict_payload)
    _write_config(explain_config_path, explain_payload)

    train_result = run_training(train_config_path, output_root=tmp_path)
    calibration_result = run_calibration(
        calibrate_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    prediction_result = run_prediction(
        predict_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=calibration_result.run_dir,
    )
    explanation_result = run_explanations(
        explain_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        prediction_file=prediction_result.prediction_file,
    )

    metrics_payload = json.loads(train_result.metrics_file.read_text(encoding="utf-8"))
    prediction_frame = pd.read_parquet(prediction_result.prediction_file)

    assert train_result.metrics_file.exists()
    assert calibration_result.metrics_file.exists()
    assert prediction_result.prediction_file.exists()
    assert explanation_result.local_explanations_file.exists()
    assert metrics_payload["primary_model"] == "logit"
    assert {"logit", "prior_rate"}.issubset(set(metrics_payload["models"]))
    assert prediction_frame["model_name"].eq("logit").all()
    assert prediction_frame["target_name"].eq(train_payload["target_name"]).all()


def test_checked_in_structural_weekly_configs_support_end_to_end_pipeline(
    tmp_path: Path,
    country_week_dataset_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[3]
    train_source = project_root / "configs" / "forecasting" / "train_country_week_onset_structural_90d.yaml"
    calibrate_source = project_root / "configs" / "forecasting" / "calibrate_country_week_onset_structural_90d.yaml"
    predict_source = project_root / "configs" / "forecasting" / "predict_country_week_onset_structural_90d.yaml"
    explain_source = project_root / "configs" / "forecasting" / "explain_country_week_onset_structural_90d.yaml"

    train_payload = yaml.safe_load(train_source.read_text(encoding="utf-8"))
    calibrate_payload = yaml.safe_load(calibrate_source.read_text(encoding="utf-8"))
    predict_payload = yaml.safe_load(predict_source.read_text(encoding="utf-8"))
    explain_payload = yaml.safe_load(explain_source.read_text(encoding="utf-8"))

    assert train_payload["label_column"] == "label_onset_90d"
    assert train_payload["horizon_days"] == 90
    assert train_payload["primary_model"] == "logit"
    assert calibrate_payload["model_name"] == "logit"
    assert predict_payload["model_name"] == "logit"
    assert explain_payload["model_name"] == "logit"

    train_payload["dataset_path"] = str(country_week_dataset_path)
    predict_payload["dataset_path"] = str(country_week_dataset_path)

    train_config_path = tmp_path / "train_country_week_onset_structural_90d.yaml"
    calibrate_config_path = tmp_path / "calibrate_country_week_onset_structural_90d.yaml"
    predict_config_path = tmp_path / "predict_country_week_onset_structural_90d.yaml"
    explain_config_path = tmp_path / "explain_country_week_onset_structural_90d.yaml"

    _write_config(train_config_path, train_payload)
    _write_config(calibrate_config_path, calibrate_payload)
    _write_config(predict_config_path, predict_payload)
    _write_config(explain_config_path, explain_payload)

    train_result = run_training(train_config_path, output_root=tmp_path)
    calibration_result = run_calibration(
        calibrate_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    prediction_result = run_prediction(
        predict_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=calibration_result.run_dir,
    )
    explanation_result = run_explanations(
        explain_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        prediction_file=prediction_result.prediction_file,
    )

    metrics_payload = json.loads(train_result.metrics_file.read_text(encoding="utf-8"))
    prediction_frame = pd.read_parquet(prediction_result.prediction_file)

    assert train_result.metrics_file.exists()
    assert calibration_result.metrics_file.exists()
    assert prediction_result.prediction_file.exists()
    assert explanation_result.local_explanations_file.exists()
    assert metrics_payload["primary_model"] == "logit"
    assert {"logit", "prior_rate"}.issubset(set(metrics_payload["models"]))
    assert prediction_frame["model_name"].eq("logit").all()
    assert prediction_frame["target_name"].eq(train_payload["target_name"]).all()


def test_checked_in_interstate_onset_weekly_configs_support_end_to_end_pipeline(
    tmp_path: Path,
    country_week_dataset_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[3]
    train_source = project_root / "configs" / "forecasting" / "train_country_week_interstate_onset_logit_30d.yaml"
    calibrate_source = project_root / "configs" / "forecasting" / "calibrate_country_week_interstate_onset_logit.yaml"
    predict_source = project_root / "configs" / "forecasting" / "predict_country_week_interstate_onset_logit.yaml"
    explain_source = project_root / "configs" / "forecasting" / "explain_country_week_interstate_onset_logit.yaml"

    train_payload = yaml.safe_load(train_source.read_text(encoding="utf-8"))
    calibrate_payload = yaml.safe_load(calibrate_source.read_text(encoding="utf-8"))
    predict_payload = yaml.safe_load(predict_source.read_text(encoding="utf-8"))
    explain_payload = yaml.safe_load(explain_source.read_text(encoding="utf-8"))

    assert train_payload["label_column"] == "label_interstate_onset_30d"
    assert train_payload["primary_model"] == "logit"
    assert calibrate_payload["model_name"] == "logit"
    assert predict_payload["model_name"] == "logit"
    assert explain_payload["model_name"] == "logit"

    interstate_dataset_path = _write_augmented_interstate_dataset(
        country_week_dataset_path,
        tmp_path / "country_week_interstate_onset.parquet",
    )

    train_payload["dataset_path"] = str(interstate_dataset_path)
    predict_payload["dataset_path"] = str(interstate_dataset_path)
    if "structural_prior" in train_payload or "structural_prior" in predict_payload:
        structural_prior_file = tmp_path / "country_week_interstate_structural_prior.parquet"
        _write_structural_prior_predictions(
            interstate_dataset_path,
            structural_prior_file,
            entity_id_column="country_iso3",
            date_column="week_start_date",
            label_column="label_interstate_onset_90d",
        )
        if "structural_prior" in train_payload:
            train_payload["structural_prior"]["prediction_file"] = str(structural_prior_file)
        if "structural_prior" in predict_payload:
            predict_payload["structural_prior"]["prediction_file"] = str(structural_prior_file)

    train_config_path = tmp_path / "train_country_week_interstate_onset_logit_30d.yaml"
    calibrate_config_path = tmp_path / "calibrate_country_week_interstate_onset_logit.yaml"
    predict_config_path = tmp_path / "predict_country_week_interstate_onset_logit.yaml"
    explain_config_path = tmp_path / "explain_country_week_interstate_onset_logit.yaml"

    _write_config(train_config_path, train_payload)
    _write_config(calibrate_config_path, calibrate_payload)
    _write_config(predict_config_path, predict_payload)
    _write_config(explain_config_path, explain_payload)

    train_result = run_training(train_config_path, output_root=tmp_path)
    calibration_result = run_calibration(
        calibrate_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    prediction_result = run_prediction(
        predict_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=calibration_result.run_dir,
    )
    explanation_result = run_explanations(
        explain_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        prediction_file=prediction_result.prediction_file,
    )

    metrics_payload = json.loads(train_result.metrics_file.read_text(encoding="utf-8"))
    prediction_frame = pd.read_parquet(prediction_result.prediction_file)

    assert train_result.metrics_file.exists()
    assert calibration_result.metrics_file.exists()
    assert prediction_result.prediction_file.exists()
    assert explanation_result.local_explanations_file.exists()
    assert metrics_payload["primary_model"] == "logit"
    assert {"logit", "prior_rate"}.issubset(set(metrics_payload["models"]))
    assert prediction_frame["model_name"].eq("logit").all()
    assert prediction_frame["target_name"].eq(train_payload["target_name"]).all()


def test_checked_in_interstate_structural_weekly_configs_support_end_to_end_pipeline(
    tmp_path: Path,
    country_week_dataset_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[3]
    train_source = project_root / "configs" / "forecasting" / "train_country_week_interstate_onset_structural_90d.yaml"
    calibrate_source = project_root / "configs" / "forecasting" / "calibrate_country_week_interstate_onset_structural_90d.yaml"
    predict_source = project_root / "configs" / "forecasting" / "predict_country_week_interstate_onset_structural_90d.yaml"
    explain_source = project_root / "configs" / "forecasting" / "explain_country_week_interstate_onset_structural_90d.yaml"

    train_payload = yaml.safe_load(train_source.read_text(encoding="utf-8"))
    calibrate_payload = yaml.safe_load(calibrate_source.read_text(encoding="utf-8"))
    predict_payload = yaml.safe_load(predict_source.read_text(encoding="utf-8"))
    explain_payload = yaml.safe_load(explain_source.read_text(encoding="utf-8"))

    assert train_payload["label_column"] == "label_interstate_onset_90d"
    assert train_payload["horizon_days"] == 90
    assert train_payload["primary_model"] == "logit"
    assert calibrate_payload["model_name"] == "logit"
    assert predict_payload["model_name"] == "logit"
    assert explain_payload["model_name"] == "logit"

    interstate_dataset_path = _write_augmented_interstate_dataset(
        country_week_dataset_path,
        tmp_path / "country_week_interstate_structural.parquet",
    )

    train_payload["dataset_path"] = str(interstate_dataset_path)
    predict_payload["dataset_path"] = str(interstate_dataset_path)

    train_config_path = tmp_path / "train_country_week_interstate_onset_structural_90d.yaml"
    calibrate_config_path = tmp_path / "calibrate_country_week_interstate_onset_structural_90d.yaml"
    predict_config_path = tmp_path / "predict_country_week_interstate_onset_structural_90d.yaml"
    explain_config_path = tmp_path / "explain_country_week_interstate_onset_structural_90d.yaml"

    _write_config(train_config_path, train_payload)
    _write_config(calibrate_config_path, calibrate_payload)
    _write_config(predict_config_path, predict_payload)
    _write_config(explain_config_path, explain_payload)

    train_result = run_training(train_config_path, output_root=tmp_path)
    calibration_result = run_calibration(
        calibrate_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    prediction_result = run_prediction(
        predict_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=calibration_result.run_dir,
    )
    explanation_result = run_explanations(
        explain_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        prediction_file=prediction_result.prediction_file,
    )

    metrics_payload = json.loads(train_result.metrics_file.read_text(encoding="utf-8"))
    prediction_frame = pd.read_parquet(prediction_result.prediction_file)

    assert train_result.metrics_file.exists()
    assert calibration_result.metrics_file.exists()
    assert prediction_result.prediction_file.exists()
    assert explanation_result.local_explanations_file.exists()
    assert metrics_payload["primary_model"] == "logit"
    assert {"logit", "prior_rate"}.issubset(set(metrics_payload["models"]))
    assert prediction_frame["model_name"].eq("logit").all()
    assert prediction_frame["target_name"].eq(train_payload["target_name"]).all()


def test_weekly_training_and_prediction_support_optional_structural_prior_score(tmp_path: Path) -> None:
    weeks = pd.date_range("2024-01-01", periods=12, freq="7D")
    rows: list[dict[str, object]] = []
    for country_iso3, offset in [("USA", 0.0), ("CAN", 1.0)]:
        for week_index, week_start in enumerate(weeks):
            label = 1 if (country_iso3 == "USA" and week_index in {4, 8}) or (country_iso3 == "CAN" and week_index in {5, 10}) else 0
            rows.append(
                {
                    "country_iso3": country_iso3,
                    "country_name": country_iso3,
                    "week_start_date": week_start,
                    "feature_a": float(week_index) + offset,
                    "feature_b": float(label),
                    "label_onset_30d": label,
                }
            )

    dataset_path = tmp_path / "country_week_structural_prior.parquet"
    pd.DataFrame(rows).to_parquet(dataset_path, index=False)

    prior_predictions_path = tmp_path / "country_week_structural_prior_predictions.parquet"
    pd.DataFrame(
        {
            "entity_id": [row["country_iso3"] for row in rows],
            "forecast_date": [row["week_start_date"] for row in rows],
            "calibrated_probability": [0.9 if row["label_onset_30d"] else 0.1 for row in rows],
        }
    ).to_parquet(prior_predictions_path, index=False)

    train_config_path = tmp_path / "train_country_week_onset_with_prior.yaml"
    calibrate_config_path = tmp_path / "calibrate_country_week_onset_with_prior.yaml"
    predict_config_path = tmp_path / "predict_country_week_onset_with_prior.yaml"

    dataset_spec = {
        "entity_id_column": "country_iso3",
        "entity_name_column": "country_name",
        "date_column": "week_start_date",
        "unit_of_analysis": "country_week",
        "group_columns": [],
        "feature_columns": ["feature_a", "feature_b"],
    }

    _write_config(
        train_config_path,
        {
            "run_name": "country_week_onset_with_prior",
            "dataset_path": str(dataset_path),
            "dataset_spec": dataset_spec,
            "target_name": "country_week_onset_30d",
            "horizon_days": 30,
            "label_column": "label_onset_30d",
            "primary_model": "logit",
            "prediction_threshold": 0.5,
            "seed": 7,
            "split": {
                "min_train_periods": 6,
                "validation_window_periods": 3,
                "step_periods": 3,
                "max_splits": 2,
            },
            "models": [
                {"name": "prior_rate", "kind": "prior_rate"},
                {"name": "logit", "kind": "logistic_regression"},
            ],
            "structural_prior": {
                "prediction_file": str(prior_predictions_path),
                "feature_name": "structural_prior_score",
            },
        },
    )
    _write_config(
        calibrate_config_path,
        {
            "run_name": "country_week_onset_with_prior",
            "model_name": "logit",
            "method": "isotonic",
            "score_column": "raw_score",
            "label_column": "label",
        },
    )
    _write_config(
        predict_config_path,
        {
            "run_name": "country_week_onset_with_prior",
            "dataset_path": str(dataset_path),
            "dataset_spec": dataset_spec,
            "model_name": "logit",
            "top_n_drivers": 5,
            "prediction_output_name": "predictions.parquet",
            "structural_prior": {
                "prediction_file": str(prior_predictions_path),
                "feature_name": "structural_prior_score",
            },
        },
    )

    train_result = run_training(train_config_path, output_root=tmp_path)
    calibration_result = run_calibration(
        calibrate_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    prediction_result = run_prediction(
        predict_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=calibration_result.run_dir,
    )

    manifest_payload = json.loads(train_result.manifest_file.read_text(encoding="utf-8"))
    prediction_frame = pd.read_parquet(prediction_result.prediction_file)

    assert "structural_prior_score" in manifest_payload["feature_columns"]
    assert manifest_payload["structural_prior"]["feature_name"] == "structural_prior_score"
    assert "structural_prior_score" in prediction_frame.columns
    assert set(prediction_frame["structural_prior_score"].unique().tolist()) == {0.1, 0.9}


def test_logit_training_records_skipped_folds_and_keeps_pipeline_working(
    tmp_path: Path,
    country_week_dataset_path: Path,
) -> None:
    dataset_path = country_week_dataset_path
    train_config_path = tmp_path / "train_country_week_logit_30d.yaml"
    calibrate_config_path = tmp_path / "calibrate_country_week_logit.yaml"
    predict_config_path = tmp_path / "predict_country_week_logit.yaml"
    explain_config_path = tmp_path / "explain_country_week_logit.yaml"

    _write_config(
        train_config_path,
        {
            "run_name": "country_week_logit_30d",
            "dataset_path": str(dataset_path),
            "dataset_spec": _country_week_dataset_spec(),
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "label_column": "label_escalation_30d",
            "primary_model": "logit",
            "prediction_threshold": 0.5,
            "seed": 7,
            "split": {
                "min_train_periods": 120,
                "validation_window_periods": 30,
                "step_periods": 30,
                "max_splits": 12,
            },
            "models": [
                {"name": "prior_rate", "kind": "prior_rate"},
                {"name": "logit", "kind": "logistic_regression"},
            ],
        },
    )
    _write_config(
        calibrate_config_path,
        {
            "run_name": "country_week_logit",
            "model_name": "logit",
            "method": "isotonic",
            "score_column": "raw_score",
            "label_column": "label",
        },
    )
    _write_config(
        predict_config_path,
        {
            "run_name": "country_week_logit",
            "dataset_path": str(dataset_path),
            "model_name": "logit",
            "top_n_drivers": 5,
            "prediction_output_name": "predictions.parquet",
            "dataset_spec": _country_week_dataset_spec(),
        },
    )
    _write_config(
        explain_config_path,
        {
            "run_name": "country_week_logit",
            "model_name": "logit",
            "top_n_drivers": 5,
        },
    )

    train_result = run_training(train_config_path, output_root=tmp_path)
    calibration_result = run_calibration(
        calibrate_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    prediction_result = run_prediction(
        predict_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=calibration_result.run_dir,
    )
    explanation_result = run_explanations(
        explain_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        prediction_file=prediction_result.prediction_file,
    )

    assert train_result.metrics_file.exists()
    assert calibration_result.calibrator_file.exists()
    assert prediction_result.prediction_file.exists()
    assert explanation_result.global_explanations_file.exists()

    metrics_payload = json.loads(train_result.metrics_file.read_text(encoding="utf-8"))
    assert "prior_rate" in metrics_payload["models"]
    assert "logit" in metrics_payload["models"]

    logit_metrics = metrics_payload["models"]["logit"]
    assert logit_metrics["skipped_folds"]
    assert any(item["reason"] == "train_fold_missing_classes" for item in logit_metrics["skipped_folds"])
    assert logit_metrics["overall"]["roc_auc"] is not None
    assert logit_metrics["overall"]["pr_auc"] is not None

    one_class_metrics = compute_classification_metrics(
        pd.DataFrame({"label": [0, 0, 0], "raw_score": [0.1, 0.2, 0.3]}),
        probability_column="raw_score",
    )
    assert one_class_metrics["roc_auc"] is None
    assert one_class_metrics["pr_auc"] is None

    prediction_frame = pd.read_parquet(prediction_result.prediction_file)
    assert "calibrated_probability" in prediction_frame.columns
    assert "feature_snapshot_hash" in prediction_frame.columns
    assert set(prediction_frame["model_name"].unique().tolist()) == {"logit"}
    assert set(prediction_frame["calibration_training_run_name"].unique().tolist()) == {"country_week_logit_30d"}

    local_explanations_frame = pd.read_parquet(explanation_result.local_explanations_file)
    assert isinstance(json.loads(local_explanations_frame.loc[0, "top_positive_drivers"]), list)
    assert isinstance(json.loads(local_explanations_frame.loc[0, "top_negative_drivers"]), list)


def test_prediction_and_explanation_fail_when_requested_model_artifact_is_missing(tmp_path: Path) -> None:
    dataset_path = tmp_path / "country_day_prediction_missing_model.parquet"
    pd.DataFrame(
        {
            "country_iso3": ["USA"] * 10,
            "as_of_date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "feature_a": [float(value) for value in range(10)],
            "label_escalation_30d": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    ).to_parquet(dataset_path, index=False)

    train_config_path = tmp_path / "train_country_week_primary_prior.yaml"
    calibrate_prior_config_path = tmp_path / "calibrate_country_week_prior.yaml"
    calibrate_logit_config_path = tmp_path / "calibrate_country_week_logit.yaml"
    predict_prior_config_path = tmp_path / "predict_country_week_prior.yaml"
    predict_missing_config_path = tmp_path / "predict_country_week_missing_logit.yaml"
    explain_missing_config_path = tmp_path / "explain_country_week_missing_logit.yaml"

    _write_config(
        train_config_path,
        {
            "run_name": "country_week_primary_prior",
            "dataset_path": str(dataset_path),
            "dataset_spec": {
                "entity_id_column": "country_iso3",
                "entity_name_column": "country_iso3",
                "date_column": "as_of_date",
                "unit_of_analysis": "country_day",
                "group_columns": [],
                "feature_columns": ["feature_a"],
            },
            "target_name": "country_day_escalation_30d",
            "horizon_days": 30,
            "label_column": "label_escalation_30d",
            "primary_model": "prior_rate",
            "prediction_threshold": 0.5,
            "seed": 7,
            "split": {
                "min_train_periods": 4,
                "validation_window_periods": 2,
                "step_periods": 2,
                "max_splits": 2,
            },
            "models": [
                {"name": "prior_rate", "kind": "prior_rate"},
                {"name": "logit", "kind": "logistic_regression"},
            ],
        },
    )
    _write_config(
        calibrate_prior_config_path,
        {
            "run_name": "country_week_prior",
            "model_name": "prior_rate",
            "method": "isotonic",
            "score_column": "raw_score",
            "label_column": "label",
        },
    )
    _write_config(
        calibrate_logit_config_path,
        {
            "run_name": "country_week_logit",
            "model_name": "logit",
            "method": "isotonic",
            "score_column": "raw_score",
            "label_column": "label",
        },
    )
    _write_config(
        predict_prior_config_path,
        {
            "run_name": "country_week_prior",
            "dataset_path": str(dataset_path),
            "model_name": "prior_rate",
            "top_n_drivers": 5,
            "prediction_output_name": "predictions.parquet",
            "dataset_spec": {
                "entity_id_column": "country_iso3",
                "entity_name_column": "country_iso3",
                "date_column": "as_of_date",
                "unit_of_analysis": "country_day",
                "group_columns": [],
                "feature_columns": ["feature_a"],
            },
        },
    )
    _write_config(
        predict_missing_config_path,
        {
            "run_name": "country_week_missing_logit",
            "dataset_path": str(dataset_path),
            "model_name": "logit",
            "top_n_drivers": 5,
            "prediction_output_name": "predictions.parquet",
            "dataset_spec": {
                "entity_id_column": "country_iso3",
                "entity_name_column": "country_iso3",
                "date_column": "as_of_date",
                "unit_of_analysis": "country_day",
                "group_columns": [],
                "feature_columns": ["feature_a"],
            },
        },
    )
    _write_config(
        explain_missing_config_path,
        {
            "run_name": "country_week_missing_logit",
            "model_name": "logit",
            "top_n_drivers": 5,
        },
    )

    train_result = run_training(train_config_path, output_root=tmp_path)
    prior_calibration_result = run_calibration(
        calibrate_prior_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    logit_calibration_result = run_calibration(
        calibrate_logit_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
    )
    prior_prediction_result = run_prediction(
        predict_prior_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=prior_calibration_result.run_dir,
    )
    with pytest.raises(ValueError, match="Calibration run was fit for model prior_rate, not logit"):
        run_prediction(
            predict_missing_config_path,
            output_root=tmp_path,
            training_run_dir=train_result.run_dir,
            calibration_run_dir=prior_calibration_result.run_dir,
        )

    with pytest.raises(ValueError, match="Prediction file was generated for model\\(s\\) \\['prior_rate'\\], not logit"):
        run_explanations(
            explain_missing_config_path,
            output_root=tmp_path,
            training_run_dir=train_result.run_dir,
            prediction_file=prior_prediction_result.prediction_file,
        )

    logit_prediction_result = run_prediction(
        predict_missing_config_path,
        output_root=tmp_path,
        training_run_dir=train_result.run_dir,
        calibration_run_dir=logit_calibration_result.run_dir,
    )
    manifest_payload = json.loads(train_result.manifest_file.read_text(encoding="utf-8"))
    Path(manifest_payload["model_files"]["logit"]).unlink()

    with pytest.raises(ValueError, match="Model artifact for logit is unavailable"):
        run_prediction(
            predict_missing_config_path,
            output_root=tmp_path,
            training_run_dir=train_result.run_dir,
            calibration_run_dir=logit_calibration_result.run_dir,
        )

    with pytest.raises(ValueError, match="Model artifact for logit is unavailable"):
        run_explanations(
            explain_missing_config_path,
            output_root=tmp_path,
            training_run_dir=train_result.run_dir,
            prediction_file=logit_prediction_result.prediction_file,
        )


def test_calibration_requires_requested_validation_model_and_ensemble_handles_missing_members(tmp_path: Path) -> None:
    dataset_path = tmp_path / "country_day_sparse.parquet"
    pd.DataFrame(
        {
            "country_iso3": ["USA"] * 10,
            "as_of_date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "feature_a": list(range(10)),
            "label_escalation_30d": [0] * 10,
        }
    ).to_parquet(dataset_path, index=False)

    train_config_path = tmp_path / "train_sparse_primary_logit.yaml"
    calibrate_config_path = tmp_path / "calibrate_sparse_logit.yaml"

    _write_config(
        train_config_path,
        {
            "run_name": "country_day_sparse_primary_logit",
            "dataset_path": str(dataset_path),
            "dataset_spec": {
                "entity_id_column": "country_iso3",
                "entity_name_column": "country_iso3",
                "date_column": "as_of_date",
                "unit_of_analysis": "country_day",
                "group_columns": [],
                "feature_columns": ["feature_a"],
            },
            "target_name": "country_day_escalation_30d",
            "horizon_days": 30,
            "label_column": "label_escalation_30d",
            "primary_model": "logit",
            "prediction_threshold": 0.5,
            "seed": 7,
            "split": {
                "min_train_periods": 4,
                "validation_window_periods": 2,
                "step_periods": 2,
                "max_splits": 2,
            },
            "models": [
                {"name": "prior_rate", "kind": "prior_rate"},
                {"name": "logit", "kind": "logistic_regression"},
            ],
            "ensemble": {
                "name": "blend",
                "members": ["prior_rate", "logit"],
                "weights": [0.5, 0.5],
            },
        },
    )
    _write_config(
        calibrate_config_path,
        {
            "run_name": "country_day_sparse_logit",
            "model_name": "logit",
            "method": "isotonic",
            "score_column": "raw_score",
            "label_column": "label",
        },
    )

    train_result = run_training(train_config_path, output_root=tmp_path)

    metrics_payload = json.loads(train_result.metrics_file.read_text(encoding="utf-8"))
    manifest_payload = json.loads(train_result.manifest_file.read_text(encoding="utf-8"))
    assert metrics_payload["primary_model"] == "logit"
    assert metrics_payload["available_validation_models"] == ["blend", "prior_rate"]
    assert metrics_payload["models"]["logit"]["status"] == "skipped_full_training_missing_classes"
    assert metrics_payload["models"]["blend"]["status"] == "trained_with_missing_members"
    assert metrics_payload["models"]["blend"]["available_members"] == ["prior_rate"]
    assert metrics_payload["models"]["blend"]["missing_members"] == ["logit"]
    assert manifest_payload["ensemble"]["members"] == ["prior_rate"]
    assert manifest_payload["ensemble"]["weights"] == [0.5]

    validation_predictions = pd.read_parquet(train_result.validation_predictions_file)
    assert sorted(validation_predictions["model_name"].unique().tolist()) == ["blend", "prior_rate"]

    with pytest.raises(ValueError, match="No validation predictions were produced for model logit"):
        run_calibration(
            calibrate_config_path,
            output_root=tmp_path,
            training_run_dir=train_result.run_dir,
        )


def test_prediction_rejects_calibration_from_a_different_training_run(tmp_path: Path) -> None:
    dataset_path = tmp_path / "country_day_two_runs.parquet"
    pd.DataFrame(
        {
            "country_iso3": ["USA"] * 10,
            "as_of_date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "feature_a": [float(value) for value in range(10)],
            "label_escalation_30d": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    ).to_parquet(dataset_path, index=False)

    train_one_config_path = tmp_path / "train_country_day_logit_one.yaml"
    train_two_config_path = tmp_path / "train_country_day_logit_two.yaml"
    calibrate_config_path = tmp_path / "calibrate_country_day_logit.yaml"
    predict_config_path = tmp_path / "predict_country_day_logit.yaml"

    common_training_payload = {
        "dataset_path": str(dataset_path),
        "dataset_spec": {
            "entity_id_column": "country_iso3",
            "entity_name_column": "country_iso3",
            "date_column": "as_of_date",
            "unit_of_analysis": "country_day",
            "group_columns": [],
            "feature_columns": ["feature_a"],
        },
        "target_name": "country_day_escalation_30d",
        "horizon_days": 30,
        "label_column": "label_escalation_30d",
        "primary_model": "logit",
        "prediction_threshold": 0.5,
        "seed": 7,
        "split": {
            "min_train_periods": 4,
            "validation_window_periods": 2,
            "step_periods": 2,
            "max_splits": 2,
        },
        "models": [{"name": "logit", "kind": "logistic_regression"}],
    }
    _write_config(train_one_config_path, {"run_name": "country_day_logit_one", **common_training_payload})
    _write_config(train_two_config_path, {"run_name": "country_day_logit_two", **common_training_payload})
    _write_config(
        calibrate_config_path,
        {
            "run_name": "country_day_logit",
            "model_name": "logit",
            "method": "isotonic",
            "score_column": "raw_score",
            "label_column": "label",
        },
    )
    _write_config(
        predict_config_path,
        {
            "run_name": "country_day_logit",
            "dataset_path": str(dataset_path),
            "model_name": "logit",
            "top_n_drivers": 5,
            "prediction_output_name": "predictions.parquet",
            "dataset_spec": common_training_payload["dataset_spec"],
        },
    )

    train_result_one = run_training(train_one_config_path, output_root=tmp_path)
    train_result_two = run_training(train_two_config_path, output_root=tmp_path)
    calibration_result_one = run_calibration(
        calibrate_config_path,
        output_root=tmp_path,
        training_run_dir=train_result_one.run_dir,
    )

    with pytest.raises(ValueError, match="Calibration run was fit from training run country_day_logit_one, not country_day_logit_two"):
        run_prediction(
            predict_config_path,
            output_root=tmp_path,
            training_run_dir=train_result_two.run_dir,
            calibration_run_dir=calibration_result_one.run_dir,
        )


def test_training_saves_final_model_when_full_data_is_trainable_but_validation_folds_are_not(tmp_path: Path) -> None:
    dataset_path = tmp_path / "country_day_late_positives.parquet"
    pd.DataFrame(
        {
            "country_iso3": ["USA"] * 6,
            "as_of_date": pd.date_range("2024-01-01", periods=6, freq="D"),
            "feature_a": [float(value) for value in range(6)],
            "label_escalation_30d": [0, 0, 0, 0, 1, 1],
        }
    ).to_parquet(dataset_path, index=False)

    train_config_path = tmp_path / "train_country_day_final_model_only.yaml"
    _write_config(
        train_config_path,
        {
            "run_name": "country_day_final_model_only",
            "dataset_path": str(dataset_path),
            "dataset_spec": {
                "entity_id_column": "country_iso3",
                "entity_name_column": "country_iso3",
                "date_column": "as_of_date",
                "unit_of_analysis": "country_day",
                "group_columns": [],
                "feature_columns": ["feature_a"],
            },
            "target_name": "country_day_escalation_30d",
            "horizon_days": 30,
            "label_column": "label_escalation_30d",
            "primary_model": "logit",
            "prediction_threshold": 0.5,
            "seed": 7,
            "split": {
                "min_train_periods": 4,
                "validation_window_periods": 1,
                "step_periods": 1,
                "max_splits": 1,
            },
            "models": [{"name": "logit", "kind": "logistic_regression"}],
        },
    )

    train_result = run_training(train_config_path, output_root=tmp_path)

    metrics_payload = json.loads(train_result.metrics_file.read_text(encoding="utf-8"))
    manifest_payload = json.loads(train_result.manifest_file.read_text(encoding="utf-8"))
    validation_predictions = pd.read_parquet(train_result.validation_predictions_file)

    assert metrics_payload["models"]["logit"]["trained_folds"] == 0
    assert metrics_payload["models"]["logit"]["status"] == "final_model_only"
    assert metrics_payload["available_validation_models"] == []
    assert Path(manifest_payload["model_files"]["logit"]).exists()
    assert validation_predictions.empty
