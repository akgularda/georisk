from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.common.logging import get_logger
from src.forecasting.calibrate import _apply_calibrator
from src.forecasting.datasets import attach_structural_prior, load_feature_frame
from src.forecasting.explain import load_model_components, summarize_signed_drivers
from src.forecasting.registry import create_run_dir, load_pickle
from src.forecasting.schemas import PredictionConfig, PredictionRunResult
from src.forecasting.train import _predict_scores
from src.forecasting.utils import load_yaml_config, project_root, read_json, stable_feature_hash

LOGGER = get_logger(__name__)


def _predict_weighted_scores(model_components, feature_frame):
    if not model_components:
        raise ValueError("No model artifacts were available for prediction.")
    total_weight = sum(weight for _, weight in model_components) or 1.0
    weighted_scores = None
    for estimator, weight in model_components:
        raw_scores = _predict_scores(estimator, feature_frame)
        if weighted_scores is None:
            weighted_scores = raw_scores * (weight / total_weight)
        else:
            weighted_scores += raw_scores * (weight / total_weight)
    return weighted_scores


def _normalize_prediction_identity(prediction_frame, dataset_spec: dict) -> None:
    entity_id_column = dataset_spec["entity_id_column"]
    entity_name_column = dataset_spec["entity_name_column"]
    date_column = dataset_spec["date_column"]
    prediction_frame["entity_id"] = prediction_frame[entity_id_column]
    prediction_frame["entity_name"] = prediction_frame[entity_name_column]
    prediction_frame["forecast_date"] = prediction_frame[date_column]


def run_prediction(
    config_path: Path,
    *,
    output_root: Path | None = None,
    training_run_dir: Path,
    calibration_run_dir: Path,
) -> PredictionRunResult:
    config = load_yaml_config(config_path, PredictionConfig)
    manifest = read_json(training_run_dir / "manifest.json")
    calibration_metrics = read_json(calibration_run_dir / "calibration_metrics.json")
    calibration_model_name = calibration_metrics.get("model_name")
    if calibration_model_name and calibration_model_name != config.model_name:
        raise ValueError(
            f"Calibration run was fit for model {calibration_model_name}, not {config.model_name}."
        )
    calibration_training_run_name = calibration_metrics.get("training_run_name")
    if calibration_training_run_name and calibration_training_run_name != manifest["run_name"]:
        raise ValueError(
            f"Calibration run was fit from training run {calibration_training_run_name}, not {manifest['run_name']}."
        )
    calibration_training_window_id = calibration_metrics.get("training_window_id")
    if calibration_training_window_id and calibration_training_window_id != manifest["training_window_id"]:
        raise ValueError(
            f"Calibration run was fit from training window {calibration_training_window_id}, not {manifest['training_window_id']}."
        )
    calibrator = load_pickle(calibration_run_dir / "calibrator.pkl")

    feature_frame = load_feature_frame(config.dataset_path, config.dataset_spec)
    feature_columns = manifest["feature_columns"]
    manifest_structural_prior = manifest.get("structural_prior")
    if manifest_structural_prior and config.structural_prior is None:
        raise ValueError("Training manifest requires a structural prior input, but prediction config does not provide one.")
    if config.structural_prior is not None:
        if manifest_structural_prior and config.structural_prior.feature_name != manifest_structural_prior.get("feature_name"):
            raise ValueError(
                "Prediction structural prior feature name does not match the training manifest."
            )
        feature_frame, augmented_feature_columns = attach_structural_prior(
            feature_frame,
            config.dataset_spec,
            config.structural_prior,
        )
        missing_columns = sorted(set(feature_columns).difference(augmented_feature_columns))
        if missing_columns:
            raise ValueError(
                f"Prediction frame is missing structural prior features required by training manifest: {missing_columns}"
            )
    dataset_spec = manifest["dataset_spec"]
    model_components = load_model_components(manifest, config.model_name)
    raw_scores = _predict_weighted_scores(model_components, feature_frame[feature_columns])
    calibrated_probabilities = _apply_calibrator(calibrator, raw_scores)
    local_positive_summaries, local_negative_summaries, _ = summarize_signed_drivers(
        model_components,
        feature_frame[feature_columns],
        top_n=config.top_n_drivers,
    )

    prediction_frame = feature_frame.copy()
    _normalize_prediction_identity(prediction_frame, dataset_spec)
    prediction_frame["raw_score"] = raw_scores
    prediction_frame["calibrated_probability"] = calibrated_probabilities
    prediction_frame["target_name"] = manifest["target_name"]
    prediction_frame["horizon_days"] = manifest["horizon_days"]
    prediction_frame["model_name"] = config.model_name
    prediction_frame["model_version"] = manifest["run_name"]
    prediction_frame["calibration_run_name"] = calibration_metrics.get("run_name", calibration_run_dir.name)
    prediction_frame["calibration_model_name"] = calibration_model_name or config.model_name
    prediction_frame["calibration_training_run_name"] = calibration_training_run_name or manifest["run_name"]
    prediction_frame["calibration_training_window_id"] = calibration_training_window_id or manifest["training_window_id"]
    prediction_frame["calibration_method"] = calibration_metrics.get("method")
    prediction_frame["training_window_id"] = manifest["training_window_id"]
    prediction_frame["top_positive_drivers"] = [json.dumps(summary) for summary in local_positive_summaries]
    prediction_frame["top_negative_drivers"] = [json.dumps(summary) for summary in local_negative_summaries]
    prediction_frame["feature_snapshot_hash"] = [
        stable_feature_hash(row)
        for row in prediction_frame[feature_columns].to_dict(orient="records")
    ]

    output_base = output_root or project_root() / "artifacts" / "forecasting"
    run_dir = create_run_dir(output_base, "predict", config.run_name)
    prediction_file = run_dir / config.prediction_output_name
    prediction_frame.to_parquet(prediction_file, index=False)
    return PredictionRunResult(run_dir=run_dir, prediction_file=prediction_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate calibrated forecasts.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--training-run-dir", required=True, type=Path)
    parser.add_argument("--calibration-run-dir", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=None)
    arguments = parser.parse_args()
    result = run_prediction(
        arguments.config,
        output_root=arguments.output_root,
        training_run_dir=arguments.training_run_dir,
        calibration_run_dir=arguments.calibration_run_dir,
    )
    LOGGER.info("Predictions written to %s", result.prediction_file)


if __name__ == "__main__":
    main()
