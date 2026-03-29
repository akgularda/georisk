from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from src.common.logging import get_logger
from src.forecasting.metrics import compute_classification_metrics
from src.forecasting.registry import create_run_dir, save_pickle
from src.forecasting.schemas import CalibrationConfig, CalibrationRunResult
from src.forecasting.utils import load_yaml_config, project_root, write_json

LOGGER = get_logger(__name__)


def _fit_calibrator(method: str, scores: np.ndarray, labels: np.ndarray) -> Any:
    if method == "isotonic":
        calibrator = IsotonicRegression(out_of_bounds="clip")
        calibrator.fit(scores, labels)
        return calibrator
    if method == "sigmoid":
        calibrator = LogisticRegression()
        calibrator.fit(scores.reshape(-1, 1), labels)
        return calibrator
    raise ValueError(f"Unsupported calibration method: {method}")


def _apply_calibrator(calibrator: Any, scores: np.ndarray) -> np.ndarray:
    if hasattr(calibrator, "predict_proba"):
        return calibrator.predict_proba(scores.reshape(-1, 1))[:, 1]
    return np.asarray(calibrator.predict(scores), dtype=float)


def run_calibration(
    config_path: Path,
    *,
    output_root: Path | None = None,
    training_run_dir: Path,
) -> CalibrationRunResult:
    config = load_yaml_config(config_path, CalibrationConfig)
    training_manifest = {}
    manifest_file = training_run_dir / "manifest.json"
    if manifest_file.exists():
        import json

        training_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    validation_predictions = pd.read_parquet(training_run_dir / "validation_predictions.parquet")
    if "model_name" in validation_predictions.columns:
        model_predictions = validation_predictions.loc[validation_predictions["model_name"] == config.model_name].copy()
        if model_predictions.empty:
            available_models = sorted(validation_predictions["model_name"].dropna().unique().tolist())
            raise ValueError(
                f"No validation predictions were produced for model {config.model_name}. "
                f"Available validation models: {available_models}"
            )
    else:
        model_predictions = validation_predictions

    scores = model_predictions[config.score_column].to_numpy(dtype=float)
    labels = model_predictions[config.label_column].to_numpy(dtype=int)

    calibrator = _fit_calibrator(config.method, scores, labels)
    calibrated_scores = _apply_calibrator(calibrator, scores)

    output_base = output_root or project_root() / "artifacts" / "forecasting"
    run_dir = create_run_dir(output_base, "calibration", config.run_name)
    calibrator_file = run_dir / "calibrator.pkl"
    metrics_file = run_dir / "calibration_metrics.json"

    save_pickle(calibrator_file, calibrator)
    metrics = compute_classification_metrics(
        model_predictions.assign(calibrated_probability=calibrated_scores),
        probability_column="calibrated_probability",
    )
    write_json(
        metrics_file,
        {
            "run_name": config.run_name,
            "method": config.method,
            "model_name": config.model_name,
            "training_run_name": training_manifest.get("run_name"),
            "training_window_id": training_manifest.get("training_window_id"),
            "metrics": metrics,
        },
    )
    return CalibrationRunResult(run_dir=run_dir, calibrator_file=calibrator_file, metrics_file=metrics_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate forecasting probabilities.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--training-run-dir", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=None)
    arguments = parser.parse_args()
    result = run_calibration(arguments.config, output_root=arguments.output_root, training_run_dir=arguments.training_run_dir)
    LOGGER.info("Calibration artifacts written to %s", result.run_dir)


if __name__ == "__main__":
    main()
