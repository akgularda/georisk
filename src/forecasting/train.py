from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.common.logging import get_logger
from src.forecasting.datasets import (
    attach_structural_prior,
    build_walk_forward_splits,
    load_feature_frame,
    prepare_training_frame,
    prepare_training_frame_from_precomputed_labels,
    summarize_label_distribution,
)
from src.forecasting.horizons import validate_horizon
from src.forecasting.metrics import compute_classification_metrics, compute_grouped_metrics
from src.forecasting.models import PriorRateModel
from src.forecasting.registry import create_run_dir, save_pickle
from src.forecasting.schemas import ModelKind, ModelSpec, TrainingConfig, TrainingRunResult
from src.forecasting.targets import get_label_definition
from src.forecasting.utils import load_yaml_config, project_root, write_json

LOGGER = get_logger(__name__)


def _make_estimator(model_spec: ModelSpec, *, seed: int) -> Any:
    imputer = SimpleImputer(strategy="constant", fill_value=0, keep_empty_features=True)
    if model_spec.kind is ModelKind.PRIOR_RATE:
        return Pipeline([("imputer", imputer), ("model", PriorRateModel())])
    if model_spec.kind is ModelKind.LOGISTIC_REGRESSION:
        params = {"max_iter": 500, "class_weight": "balanced", **model_spec.params}
        return Pipeline([("imputer", imputer), ("model", LogisticRegression(random_state=seed, **params))])
    if model_spec.kind is ModelKind.ELASTIC_NET:
        params = {
            "max_iter": 1000,
            "class_weight": "balanced",
            "penalty": "elasticnet",
            "solver": "saga",
            "l1_ratio": 0.5,
            **model_spec.params,
        }
        return Pipeline([("imputer", imputer), ("model", LogisticRegression(random_state=seed, **params))])
    if model_spec.kind is ModelKind.RANDOM_FOREST:
        params = {"n_estimators": 100, "class_weight": "balanced", **model_spec.params}
        return Pipeline([("imputer", imputer), ("model", RandomForestClassifier(random_state=seed, **params))])
    if model_spec.kind is ModelKind.LIGHTGBM:
        params = {
            "n_estimators": 80,
            "learning_rate": 0.05,
            "num_leaves": 15,
            "objective": "binary",
            "random_state": seed,
            "verbose": -1,
            **model_spec.params,
        }
        return Pipeline([("imputer", imputer), ("model", LGBMClassifier(**params))])
    raise ValueError(f"Unsupported model kind: {model_spec.kind}")


def _predict_scores(estimator: Any, feature_frame: pd.DataFrame) -> np.ndarray:
    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(feature_frame)[:, 1]
    if hasattr(estimator, "decision_function"):
        raw = estimator.decision_function(feature_frame)
        return 1.0 / (1.0 + np.exp(-raw))
    raise TypeError("Estimator does not support probability prediction")


def _should_skip_fold(model_spec: ModelSpec, train_fold: pd.DataFrame, validation_fold: pd.DataFrame) -> tuple[bool, str | None, dict[str, int], dict[str, int]]:
    train_counts = summarize_label_distribution(train_fold)
    validation_counts = summarize_label_distribution(validation_fold)
    if validation_counts["row_count"] == 0:
        return True, "validation_fold_empty", train_counts, validation_counts
    if train_counts["row_count"] == 0:
        return True, "train_fold_empty", train_counts, validation_counts
    if model_spec.kind is not ModelKind.PRIOR_RATE and train_counts["class_count"] < 2:
        return True, "train_fold_missing_classes", train_counts, validation_counts
    return False, None, train_counts, validation_counts


def _metadata_columns(dataset_spec, frame: pd.DataFrame) -> list[str]:
    candidates = [
        dataset_spec.entity_id_column,
        dataset_spec.entity_name_column,
        dataset_spec.date_column,
        *dataset_spec.group_columns,
    ]
    ordered: list[str] = []
    for column in candidates:
        if column in frame.columns and column not in ordered:
            ordered.append(column)
    return ordered


def _build_ensemble_predictions(
    validation_predictions_by_model: dict[str, pd.DataFrame],
    ensemble_spec,
    metadata_columns: list[str],
) -> tuple[pd.DataFrame | None, list[str], list[float], list[str]]:
    weights = ensemble_spec.weights or [1.0] * len(ensemble_spec.members)
    keys = metadata_columns + ["label", "next_event_date", "split_id", "target_name", "horizon_days"]
    merged = None
    available_members: list[str] = []
    available_weights: list[float] = []
    missing_members: list[str] = []
    for member_name, weight in zip(ensemble_spec.members, weights, strict=False):
        member_predictions = validation_predictions_by_model.get(member_name)
        if member_predictions is None:
            missing_members.append(member_name)
            continue
        member_frame = member_predictions[keys + ["raw_score"]].rename(
            columns={"raw_score": f"raw_score__{member_name}"}
        )
        merged = member_frame if merged is None else merged.merge(member_frame, on=keys, how="inner")
        available_members.append(member_name)
        available_weights.append(weight)

    if merged is None:
        return None, available_members, available_weights, missing_members

    score_columns = [f"raw_score__{member_name}" for member_name in available_members]
    total_weight = sum(available_weights) or 1.0
    normalized_weights = np.asarray(available_weights, dtype=float) / total_weight
    merged["raw_score"] = merged[score_columns].to_numpy(dtype=float) @ normalized_weights
    merged["model_name"] = ensemble_spec.name
    return merged[keys + ["raw_score", "model_name"]], available_members, available_weights, missing_members


def run_training(config_path: Path, *, output_root: Path | None = None) -> TrainingRunResult:
    config = load_yaml_config(config_path, TrainingConfig)
    validate_horizon(config.horizon_days)
    feature_frame = load_feature_frame(config.dataset_path, config.dataset_spec)
    feature_columns = list(config.dataset_spec.feature_columns)
    if config.structural_prior is not None:
        feature_frame, feature_columns = attach_structural_prior(
            feature_frame,
            config.dataset_spec,
            config.structural_prior,
        )
    label_definition = None
    if config.label_column is not None:
        training_frame = prepare_training_frame_from_precomputed_labels(
            feature_frame,
            config.dataset_spec,
            label_column=config.label_column,
            next_event_date_column=config.next_event_date_column,
        )
    else:
        label_definition = config.label_definition or get_label_definition(config.target_name)
        training_frame = prepare_training_frame(feature_frame, config.dataset_spec, label_definition, config.horizon_days)
    splits = build_walk_forward_splits(
        training_frame,
        config.dataset_spec,
        min_train_periods=config.split.min_train_periods,
        validation_window_periods=config.split.validation_window_periods,
        step_periods=config.split.step_periods,
        max_splits=config.split.max_splits,
    )
    if not splits:
        raise ValueError("No walk-forward splits were generated.")

    output_base = output_root or project_root() / "artifacts" / "forecasting"
    run_dir = create_run_dir(output_base, "train", config.run_name)
    metadata_columns = _metadata_columns(config.dataset_spec, training_frame)

    validation_predictions_by_model: dict[str, pd.DataFrame] = {}
    metrics_payload: dict[str, Any] = {"models": {}}
    model_files: dict[str, str] = {}
    full_training_counts = summarize_label_distribution(training_frame)
    resolved_ensemble_spec: dict[str, Any] | None = None
    validation_prediction_columns = metadata_columns + [
        "label",
        "next_event_date",
        "raw_score",
        "model_name",
        "split_id",
        "target_name",
        "horizon_days",
    ]

    for model_spec in config.models:
        LOGGER.info("Training model %s", model_spec.name)
        fold_predictions: list[pd.DataFrame] = []
        skipped_folds: list[dict[str, Any]] = []
        for split in splits:
            train_mask = training_frame[config.dataset_spec.date_column].between(split.train_start, split.train_end)
            validation_mask = training_frame[config.dataset_spec.date_column].between(split.validation_start, split.validation_end)
            train_fold = training_frame.loc[train_mask]
            validation_fold = training_frame.loc[validation_mask]
            should_skip, skip_reason, train_counts, validation_counts = _should_skip_fold(
                model_spec,
                train_fold,
                validation_fold,
            )
            if should_skip:
                skipped_folds.append(
                    {
                        "split_id": split.split_id,
                        "reason": skip_reason,
                        "train_row_count": train_counts["row_count"],
                        "train_positive_count": train_counts["positive_count"],
                        "train_negative_count": train_counts["negative_count"],
                        "validation_row_count": validation_counts["row_count"],
                        "validation_positive_count": validation_counts["positive_count"],
                        "validation_negative_count": validation_counts["negative_count"],
                    }
                )
                continue

            estimator = _make_estimator(model_spec, seed=config.seed)
            estimator.fit(train_fold[feature_columns], train_fold["label"])
            raw_scores = _predict_scores(estimator, validation_fold[feature_columns])

            fold_frame = validation_fold[metadata_columns + ["label", "next_event_date"]].copy()
            fold_frame["raw_score"] = raw_scores
            fold_frame["model_name"] = model_spec.name
            fold_frame["split_id"] = split.split_id
            fold_frame["target_name"] = config.target_name
            fold_frame["horizon_days"] = config.horizon_days
            fold_predictions.append(fold_frame)

        if fold_predictions:
            combined_folds = pd.concat(fold_predictions, ignore_index=True)
            validation_predictions_by_model[model_spec.name] = combined_folds
            metrics_payload["models"][model_spec.name] = {
                "overall": compute_classification_metrics(
                    combined_folds,
                    probability_column="raw_score",
                    threshold=config.prediction_threshold,
                ),
                "by_group": compute_grouped_metrics(
                    combined_folds,
                    probability_column="raw_score",
                    group_columns=config.dataset_spec.group_columns,
                    threshold=config.prediction_threshold,
                ),
                "skipped_folds": skipped_folds,
                "trained_folds": len(fold_predictions),
                "status": "trained",
            }
        else:
            metrics_payload["models"][model_spec.name] = {
                "overall": None,
                "by_group": {},
                "skipped_folds": skipped_folds,
                "trained_folds": 0,
                "status": "no_trainable_folds",
            }

        if model_spec.kind is not ModelKind.PRIOR_RATE and full_training_counts["class_count"] < 2:
            metrics_payload["models"][model_spec.name].update(
                {
                    "status": "skipped_full_training_missing_classes",
                }
            )
            continue

        final_estimator = _make_estimator(model_spec, seed=config.seed)
        final_estimator.fit(training_frame[feature_columns], training_frame["label"])
        model_file = run_dir / "models" / f"{model_spec.name}.pkl"
        save_pickle(model_file, final_estimator)
        model_files[model_spec.name] = str(model_file.resolve())
        if not fold_predictions:
            metrics_payload["models"][model_spec.name]["status"] = "final_model_only"

    if config.ensemble is not None:
        ensemble_predictions, available_members, available_weights, missing_members = _build_ensemble_predictions(
            validation_predictions_by_model,
            config.ensemble,
            metadata_columns,
        )
        if ensemble_predictions is None:
            metrics_payload["models"][config.ensemble.name] = {
                "overall": None,
                "by_group": {},
                "skipped_folds": [],
                "trained_folds": 0,
                "status": "no_available_members",
                "available_members": available_members,
                "missing_members": missing_members,
            }
        else:
            validation_predictions_by_model[config.ensemble.name] = ensemble_predictions
            resolved_ensemble_spec = {
                "name": config.ensemble.name,
                "members": available_members,
                "weights": available_weights,
            }
            metrics_payload["models"][config.ensemble.name] = {
                "overall": compute_classification_metrics(
                    ensemble_predictions,
                    probability_column="raw_score",
                    threshold=config.prediction_threshold,
                ),
                "by_group": compute_grouped_metrics(
                    ensemble_predictions,
                    probability_column="raw_score",
                    group_columns=config.dataset_spec.group_columns,
                    threshold=config.prediction_threshold,
                ),
                "skipped_folds": [],
                "trained_folds": 1,
                "status": "trained_with_missing_members" if missing_members else "trained",
                "available_members": available_members,
                "missing_members": missing_members,
            }

    validation_predictions = pd.concat(validation_predictions_by_model.values(), ignore_index=True).sort_values(
        by=["model_name", *metadata_columns],
        kind="mergesort",
    ) if validation_predictions_by_model else pd.DataFrame(columns=validation_prediction_columns)
    available_validation_models = sorted(validation_predictions_by_model)
    if not available_validation_models:
        if not model_files:
            raise ValueError("No validation predictions or full-data models were produced for any model.")
        LOGGER.warning("No validation predictions were produced. Saved full-data models: %s", ", ".join(sorted(model_files)))
    elif config.primary_model not in validation_predictions_by_model:
        LOGGER.warning(
            "Primary model %s produced no validation predictions. Available validation models: %s",
            config.primary_model,
            ", ".join(available_validation_models),
        )

    validation_predictions_file = run_dir / "validation_predictions.parquet"
    validation_predictions.to_parquet(validation_predictions_file, index=False)

    training_window_id = (
        f"{training_frame[config.dataset_spec.date_column].min()}_"
        f"{training_frame[config.dataset_spec.date_column].max()}"
    )
    manifest = {
        "run_name": config.run_name,
        "target_name": config.target_name,
        "horizon_days": config.horizon_days,
        "label_definition": label_definition.model_dump(mode="json") if label_definition is not None else None,
        "label_column": config.label_column,
        "feature_columns": feature_columns,
        "dataset_spec": config.dataset_spec.model_dump(mode="json"),
        "primary_model": config.primary_model,
        "available_validation_models": available_validation_models,
        "model_files": model_files,
        "feature_preprocessor": {"name": "simple_imputer", "strategy": "constant", "fill_value": 0},
        "configured_ensemble": config.ensemble.model_dump(mode="json") if config.ensemble is not None else None,
        "ensemble": resolved_ensemble_spec,
        "structural_prior": config.structural_prior.model_dump(mode="json") if config.structural_prior is not None else None,
        "training_window_id": training_window_id,
    }
    manifest_file = run_dir / "manifest.json"
    metrics_file = run_dir / "metrics.json"
    metrics_payload["primary_model"] = config.primary_model
    metrics_payload["available_validation_models"] = available_validation_models
    write_json(manifest_file, manifest)
    write_json(metrics_file, metrics_payload)

    return TrainingRunResult(
        run_dir=run_dir,
        manifest_file=manifest_file,
        metrics_file=metrics_file,
        validation_predictions_file=validation_predictions_file,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train forecasting models.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", type=Path, default=None)
    arguments = parser.parse_args()
    result = run_training(arguments.config, output_root=arguments.output_root)
    LOGGER.info("Training artifacts written to %s", result.run_dir)


if __name__ == "__main__":
    main()
