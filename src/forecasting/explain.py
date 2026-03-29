from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.pipeline import Pipeline

from src.common.logging import get_logger
from src.forecasting.registry import create_run_dir, load_pickle
from src.forecasting.schemas import ExplanationConfig, ExplanationRunResult
from src.forecasting.utils import load_yaml_config, project_root, read_json, write_json

LOGGER = get_logger(__name__)


def _prepare_feature_frame_for_estimator(estimator: Any, feature_frame: pd.DataFrame) -> tuple[Any, pd.DataFrame]:
    if isinstance(estimator, Pipeline):
        preprocessor = estimator[:-1]
        if len(preprocessor.steps) > 0:
            transformed = preprocessor.transform(feature_frame)
            if hasattr(transformed, "toarray"):
                transformed = transformed.toarray()
            feature_frame = pd.DataFrame(transformed, columns=list(feature_frame.columns), index=feature_frame.index)
        estimator = estimator.steps[-1][1]
    return estimator, feature_frame


def _compute_single_contributions(estimator: Any, feature_frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    estimator, feature_frame = _prepare_feature_frame_for_estimator(estimator, feature_frame)
    if isinstance(estimator, LGBMClassifier):
        contributions = estimator.predict(feature_frame, pred_contrib=True)
        return np.asarray(contributions[:, :-1], dtype=float), list(feature_frame.columns)
    if hasattr(estimator, "coef_"):
        coefficients = np.asarray(estimator.coef_[0], dtype=float)
        return feature_frame.to_numpy(dtype=float) * coefficients, list(feature_frame.columns)
    if hasattr(estimator, "feature_importances_"):
        importances = np.asarray(estimator.feature_importances_, dtype=float)
        tiled = np.tile(importances, (len(feature_frame), 1))
        return tiled, list(feature_frame.columns)
    return np.zeros((len(feature_frame), len(feature_frame.columns))), list(feature_frame.columns)


def _normalize_components(
    model_components: list[tuple[Any, float]],
    feature_frame: pd.DataFrame,
) -> tuple[np.ndarray, list[str]]:
    total_weight = sum(weight for _, weight in model_components) or 1.0
    combined: np.ndarray | None = None
    feature_names: list[str] = list(feature_frame.columns)

    for estimator, weight in model_components:
        contributions, feature_names = _compute_single_contributions(estimator, feature_frame)
        weighted = contributions * (weight / total_weight)
        combined = weighted if combined is None else combined + weighted

    if combined is None:
        combined = np.zeros((len(feature_frame), len(feature_frame.columns)), dtype=float)
    return combined, feature_names


def summarize_signed_drivers(
    model_components: list[tuple[Any, float]],
    feature_frame: pd.DataFrame,
    *,
    top_n: int,
) -> tuple[list[list[dict[str, float | str]]], list[list[dict[str, float | str]]], list[dict[str, float | str]]]:
    contributions, feature_names = _normalize_components(model_components, feature_frame)
    local_positive_summaries: list[list[dict[str, float | str]]] = []
    local_negative_summaries: list[list[dict[str, float | str]]] = []
    for row in contributions:
        positive_indices = [index for index in np.argsort(row)[::-1] if row[index] > 0][:top_n]
        negative_indices = [index for index in np.argsort(row) if row[index] < 0][:top_n]
        local_positive_summaries.append(
            [{"feature": feature_names[index], "contribution": float(row[index])} for index in positive_indices]
        )
        local_negative_summaries.append(
            [{"feature": feature_names[index], "contribution": float(row[index])} for index in negative_indices]
        )

    global_importance = np.mean(np.abs(contributions), axis=0)
    ordered_global_indices = np.argsort(global_importance)[::-1][:top_n]
    global_summary = [
        {"feature": feature_names[index], "mean_absolute_contribution": float(global_importance[index])}
        for index in ordered_global_indices
    ]
    return local_positive_summaries, local_negative_summaries, global_summary


def load_model_components(manifest: dict[str, Any], model_name: str) -> list[tuple[Any, float]]:
    model_files = manifest.get("model_files", {})

    def _load_component(component_name: str) -> Any | None:
        model_file = model_files.get(component_name)
        if not model_file:
            return None
        path = Path(model_file)
        if not path.exists():
            return None
        return load_pickle(path)

    ensemble_spec = manifest.get("ensemble")
    if ensemble_spec and ensemble_spec["name"] == model_name:
        weights = ensemble_spec.get("weights") or [1.0] * len(ensemble_spec["members"])
        model_components: list[tuple[Any, float]] = []
        missing_members: list[str] = []
        for member_name, weight in zip(ensemble_spec["members"], weights, strict=False):
            estimator = _load_component(member_name)
            if estimator is None:
                missing_members.append(member_name)
                continue
            model_components.append((estimator, float(weight)))
        if model_components:
            if missing_members:
                LOGGER.warning(
                    "Ensemble %s is missing member artifacts for %s; using available members only.",
                    model_name,
                    ", ".join(missing_members),
                )
            return model_components

    estimator = _load_component(model_name)
    if estimator is not None:
        return [(estimator, 1.0)]

    available_models = sorted(name for name, model_file in model_files.items() if model_file and Path(model_file).exists())
    raise ValueError(
        f"Model artifact for {model_name} is unavailable. Available model artifacts: {available_models}"
    )


def run_explanations(
    config_path: Path,
    *,
    output_root: Path | None = None,
    training_run_dir: Path,
    prediction_file: Path,
) -> ExplanationRunResult:
    config = load_yaml_config(config_path, ExplanationConfig)
    manifest = read_json(training_run_dir / "manifest.json")
    prediction_frame = pd.read_parquet(prediction_file)
    if "model_name" in prediction_frame.columns:
        prediction_models = sorted(prediction_frame["model_name"].dropna().astype(str).unique().tolist())
        if prediction_models != [config.model_name]:
            raise ValueError(
                f"Prediction file was generated for model(s) {prediction_models}, not {config.model_name}."
            )
    if "model_version" in prediction_frame.columns:
        prediction_versions = sorted(prediction_frame["model_version"].dropna().astype(str).unique().tolist())
        if prediction_versions != [manifest["run_name"]]:
            raise ValueError(
                f"Prediction file was generated from training run(s) {prediction_versions}, not {manifest['run_name']}."
            )
    feature_columns = manifest["feature_columns"]
    model_components = load_model_components(manifest, config.model_name)

    local_positive_summaries, local_negative_summaries, global_summary = summarize_signed_drivers(
        model_components,
        prediction_frame[feature_columns],
        top_n=config.top_n_drivers,
    )
    output_base = output_root or project_root() / "artifacts" / "forecasting"
    run_dir = create_run_dir(output_base, "explanations", config.run_name)
    global_explanations_file = run_dir / "global_explanations.json"
    local_explanations_file = run_dir / "local_explanations.parquet"

    write_json(global_explanations_file, {"model_name": config.model_name, "global_importance": global_summary})
    pd.DataFrame(
        {
            "entity_id": prediction_frame["entity_id"],
            "entity_name": prediction_frame["entity_name"],
            "forecast_date": prediction_frame["forecast_date"],
            "top_positive_drivers": [json.dumps(summary) for summary in local_positive_summaries],
            "top_negative_drivers": [json.dumps(summary) for summary in local_negative_summaries],
        }
    ).to_parquet(local_explanations_file, index=False)

    return ExplanationRunResult(
        run_dir=run_dir,
        global_explanations_file=global_explanations_file,
        local_explanations_file=local_explanations_file,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate forecasting explanations.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--training-run-dir", required=True, type=Path)
    parser.add_argument("--prediction-file", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=None)
    arguments = parser.parse_args()
    result = run_explanations(
        arguments.config,
        output_root=arguments.output_root,
        training_run_dir=arguments.training_run_dir,
        prediction_file=arguments.prediction_file,
    )
    LOGGER.info("Explanation artifacts written to %s", result.run_dir)


if __name__ == "__main__":
    main()
