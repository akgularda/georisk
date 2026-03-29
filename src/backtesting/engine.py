from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.backtesting.alerting import build_alert_table
from src.backtesting.evaluators import (
    evaluate_prediction_frame,
    select_operating_threshold,
    summarize_alert_metrics,
    summarize_model_comparison,
    summarize_ranking_metrics,
)
from src.backtesting.experiments import build_experiment_manifest
from src.backtesting.plots import write_precision_recall_svg, write_probability_distribution_svg
from src.backtesting.registry import resolve_backtest_run_dir, resolve_replay_run_dir
from src.backtesting.reports import write_backtest_report, write_replay_report
from src.backtesting.schemas import BacktestConfig, BacktestRunResult, ReplayConfig, ReplayRunResult
from src.backtesting.windows import build_backtest_windows
from src.forecasting.calibrate import _apply_calibrator, _fit_calibrator
from src.forecasting.datasets import (
    attach_structural_prior,
    load_feature_frame,
    prepare_training_frame,
    prepare_training_frame_from_precomputed_labels,
)
from src.forecasting.explain import summarize_signed_drivers
from src.forecasting.registry import save_pickle
from src.forecasting.targets import get_label_definition
from src.forecasting.train import _make_estimator, _predict_scores
from src.forecasting.utils import load_yaml_config, read_json, stable_feature_hash, write_json


def _training_frame_from_config(config: BacktestConfig) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    feature_frame = load_feature_frame(config.dataset_path, config.dataset_spec)
    feature_columns = list(config.dataset_spec.feature_columns)
    if config.structural_prior is not None:
        feature_frame, feature_columns = attach_structural_prior(
            feature_frame,
            config.dataset_spec,
            config.structural_prior,
        )
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
    return feature_frame, training_frame, feature_columns


def _standardize_prediction_frame(frame: pd.DataFrame, *, dataset_spec, target_name: str, horizon_days: int, model_name: str) -> pd.DataFrame:
    standardized = frame.copy()
    standardized["entity_id"] = standardized[dataset_spec.entity_id_column]
    standardized["entity_name"] = standardized[dataset_spec.entity_name_column]
    standardized["forecast_date"] = pd.to_datetime(standardized[dataset_spec.date_column]).dt.date
    standardized["target_name"] = target_name
    standardized["horizon_days"] = horizon_days
    standardized["model_name"] = model_name
    return standardized


def _resolve_requested_models(
    *,
    primary_model: str,
    baseline_model: str | None,
    available_models: list[str],
) -> tuple[str, str | None]:
    if primary_model not in available_models:
        raise ValueError(f"Configured primary model `{primary_model}` was not produced. Available models: {available_models}")
    if baseline_model is not None:
        if baseline_model not in available_models:
            raise ValueError(
                f"Configured baseline model `{baseline_model}` was not produced. Available models: {available_models}"
            )
        return primary_model, baseline_model
    if "prior_rate" in available_models:
        return primary_model, "prior_rate"
    return primary_model, None


def run_backtest(config_path: Path, *, output_root: Path | None = None) -> BacktestRunResult:
    config = load_yaml_config(config_path, BacktestConfig)
    _, training_frame, feature_columns = _training_frame_from_config(config)
    windows = build_backtest_windows(training_frame, config.dataset_spec, config.split)
    if not windows:
        raise ValueError("No backtest windows were generated.")

    run_dir = resolve_backtest_run_dir(config.run_name, output_root=output_root)
    windows_file = run_dir / "windows.json"
    metrics_file = run_dir / "metrics.json"
    predictions_file = run_dir / "predictions.parquet"
    alerts_file = run_dir / "alerts.parquet"
    report_file = run_dir / "summary.md"

    all_predictions: list[pd.DataFrame] = []
    model_metrics: dict[str, Any] = {}
    available_models: list[str] = []

    for model_spec in config.models:
        fold_predictions: list[pd.DataFrame] = []
        last_calibrator: Any | None = None
        for window in windows:
            train_mask = training_frame[config.dataset_spec.date_column].between(window.train_start, window.train_end)
            validation_mask = training_frame[config.dataset_spec.date_column].between(window.validation_start, window.validation_end)
            train_fold = training_frame.loc[train_mask]
            validation_fold = training_frame.loc[validation_mask]
            if validation_fold.empty:
                continue
            if train_fold["label"].nunique() < 2 and model_spec.kind.value != "prior_rate":
                continue

            estimator = _make_estimator(model_spec, seed=config.seed)
            estimator.fit(train_fold[feature_columns], train_fold["label"])
            train_scores = _predict_scores(estimator, train_fold[feature_columns])
            validation_scores = _predict_scores(estimator, validation_fold[feature_columns])
            fold_frame = validation_fold.copy()
            fold_frame["raw_score"] = validation_scores
            if train_fold["label"].nunique() >= 2:
                calibrator = _fit_calibrator(
                    config.calibration_method,
                    train_scores,
                    train_fold["label"].to_numpy(dtype=int),
                )
                fold_frame["calibrated_probability"] = _apply_calibrator(calibrator, validation_scores)
                last_calibrator = calibrator
            else:
                fold_frame["calibrated_probability"] = fold_frame["raw_score"].astype(float)
            fold_frame["split_id"] = window.split_id
            fold_predictions.append(
                _standardize_prediction_frame(
                    fold_frame,
                    dataset_spec=config.dataset_spec,
                    target_name=config.target_name,
                    horizon_days=config.horizon_days,
                    model_name=model_spec.name,
                )
            )

        if not fold_predictions:
            continue

        combined = pd.concat(fold_predictions, ignore_index=True)
        if last_calibrator is not None:
            save_pickle(run_dir / "calibrators" / f"{model_spec.name}.pkl", last_calibrator)

        final_estimator = _make_estimator(model_spec, seed=config.seed)
        if training_frame["label"].nunique() >= 2 or model_spec.kind.value == "prior_rate":
            final_estimator.fit(training_frame[feature_columns], training_frame["label"])
            local_positive_summaries, local_negative_summaries, _ = summarize_signed_drivers(
                [(final_estimator, 1.0)],
                combined[feature_columns],
                top_n=5,
            )
        else:
            local_positive_summaries = [[] for _ in range(len(combined))]
            local_negative_summaries = [[] for _ in range(len(combined))]

        combined["top_positive_drivers"] = [str(summary) for summary in local_positive_summaries]
        combined["top_negative_drivers"] = [str(summary) for summary in local_negative_summaries]
        combined["feature_snapshot_hash"] = [
            stable_feature_hash(row) for row in combined[feature_columns].to_dict(orient="records")
        ]
        all_predictions.append(combined)
        available_models.append(model_spec.name)
        model_metrics[model_spec.name] = evaluate_prediction_frame(
            combined,
            probability_column="calibrated_probability",
            threshold=config.prediction_threshold,
            group_columns=config.dataset_spec.group_columns,
        )

    if not all_predictions:
        raise ValueError("No backtest predictions were generated.")

    predictions = pd.concat(all_predictions, ignore_index=True).sort_values(
        by=["model_name", "entity_id", "forecast_date"],
        kind="mergesort",
    )
    predictions.to_parquet(predictions_file, index=False)

    primary_model_name, baseline_model_name = _resolve_requested_models(
        primary_model=config.primary_model,
        baseline_model=config.baseline_model,
        available_models=available_models,
    )
    primary_predictions = predictions.loc[predictions["model_name"] == primary_model_name].copy()
    threshold_summary = select_operating_threshold(
        primary_predictions,
        gap_days=config.alert_gap_days or config.horizon_days,
    )
    alerts = build_alert_table(
        primary_predictions,
        threshold=float(threshold_summary["alert_threshold"]),
        gap_days=config.alert_gap_days or config.horizon_days,
    )
    alerts.to_parquet(alerts_file, index=False)
    ranking_metrics = summarize_ranking_metrics(
        primary_predictions,
        publish_threshold=float(threshold_summary["publish_threshold"]),
    )
    alert_metrics = summarize_alert_metrics(alerts)
    alert_metrics.update(
        {
            "publish_threshold": float(threshold_summary["publish_threshold"]),
            "alert_threshold": float(threshold_summary["alert_threshold"]),
            "recall_at_5": ranking_metrics["recall_at_5"],
            "recall_at_10": ranking_metrics["recall_at_10"],
            "no_clear_leader_rate": ranking_metrics["no_clear_leader_rate"],
        }
    )

    plots_dir = run_dir / "plots"
    probability_plot_file = write_probability_distribution_svg(primary_predictions, plots_dir / "probability_distribution.svg")
    precision_recall_plot_file = write_precision_recall_svg(primary_predictions, plots_dir / "precision_recall.svg")
    plot_references = {
        "probability_distribution": str(probability_plot_file),
        "precision_recall": str(precision_recall_plot_file),
    }
    comparison_summary = summarize_model_comparison(model_metrics, baseline_model=baseline_model_name)

    manifest = build_experiment_manifest(
        config,
        windows=[window.__dict__ for window in windows],
        available_models=available_models,
    )
    manifest["plots"] = plot_references
    write_json(windows_file, manifest)
    write_json(
        metrics_file,
        {
            "models": model_metrics,
            "alerts": alert_metrics,
            "primary_model": primary_model_name,
            "baseline_model": baseline_model_name,
            "requested_primary_model": config.primary_model,
            "requested_baseline_model": config.baseline_model,
            "comparison": comparison_summary,
            "plots": plot_references,
            "calibration": {
                "method": config.calibration_method,
                "evaluation_strategy": "per_fold_training_slice",
            },
        },
    )
    write_backtest_report(
        report_file,
        run_name=config.run_name,
        target_name=config.target_name,
        primary_model=primary_model_name,
        baseline_model=baseline_model_name,
        model_metrics=model_metrics,
        comparison_summary=comparison_summary,
        alert_metrics=alert_metrics,
        calibration_method=config.calibration_method,
        plot_references=plot_references,
    )
    return BacktestRunResult(
        run_dir=run_dir,
        predictions_file=predictions_file,
        alerts_file=alerts_file,
        metrics_file=metrics_file,
        report_file=report_file,
        windows_file=windows_file,
    )


def run_replay(
    config_path: Path,
    *,
    output_root: Path | None = None,
) -> ReplayRunResult:
    config = load_yaml_config(config_path, ReplayConfig)
    backtest_run_dir = resolve_backtest_run_dir(config.backtest_run_name, output_root=output_root)
    metrics = read_json(backtest_run_dir / "metrics.json")
    replay_model = config.model_name or metrics["primary_model"]
    comparison = metrics.get("comparison") or {}
    top_model = comparison.get("top_model") or {}
    predictions = pd.read_parquet(backtest_run_dir / "predictions.parquet")
    alerts = pd.read_parquet(backtest_run_dir / "alerts.parquet")

    predictions["forecast_date"] = pd.to_datetime(predictions["forecast_date"]).dt.date
    alerts["forecast_date"] = pd.to_datetime(alerts["forecast_date"]).dt.date
    available_models = sorted(predictions["model_name"].dropna().unique().tolist())
    if replay_model not in available_models:
        raise ValueError(
            f"Replay model `{replay_model}` was not produced by backtest `{config.backtest_run_name}`. "
            f"Available models: {available_models}"
        )
    replay_predictions = predictions.loc[
        (predictions["model_name"] == replay_model) & (predictions["entity_id"] == config.entity_id)
    ].copy()
    replay_predictions = replay_predictions.merge(
        alerts[["entity_id", "forecast_date", "is_alert", "alert_outcome"]],
        on=["entity_id", "forecast_date"],
        how="left",
    )
    replay_predictions = replay_predictions.sort_values(by="forecast_date", ascending=False).head(config.max_rows)

    run_dir = resolve_replay_run_dir(config.run_name, output_root=output_root)
    replay_file = write_replay_report(
        run_dir / f"{config.entity_id.lower()}_replay.md",
        entity_id=config.entity_id,
        model_name=replay_model,
        comparison_top_model=top_model.get("model_name"),
        replay_rows=replay_predictions.to_dict(orient="records"),
    )
    return ReplayRunResult(run_dir=run_dir, replay_file=replay_file)
