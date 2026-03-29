from __future__ import annotations

import json
from pathlib import Path

import pytest
import pandas as pd
import yaml

from src.backtesting.engine import run_backtest, run_replay
from src.backtesting.evaluators import summarize_model_comparison
from src.backtesting.reports import write_backtest_report
from src.data_platform.orchestration.pipeline import run_country_week_features_pipeline


def _write_minimal_backtest_dataset(tmp_path: Path) -> Path:
    dataset_path = tmp_path / "toy_backtest.parquet"
    frame = pd.DataFrame(
        {
            "entity_id": ["IRN"] * 6,
            "entity_name": ["Iran"] * 6,
            "as_of_date": pd.date_range("2025-01-01", periods=6, freq="7D"),
            "feature_1": [0.0, 1.0, 0.2, 1.2, 0.4, 1.4],
            "label": [0, 1, 0, 1, 0, 1],
        }
    )
    frame.to_parquet(dataset_path, index=False)
    return dataset_path


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


def _write_backtest_config(
    tmp_path: Path,
    *,
    dataset_path: Path,
    run_name: str,
    models: list[dict[str, object]],
    primary_model: str,
    baseline_model: str | None = None,
) -> Path:
    config_path = tmp_path / f"{run_name}.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "run_name": run_name,
                "dataset_path": str(dataset_path),
                "dataset_spec": {
                    "entity_id_column": "entity_id",
                    "entity_name_column": "entity_name",
                    "date_column": "as_of_date",
                    "unit_of_analysis": "country_week",
                    "feature_columns": ["feature_1"],
                    "group_columns": [],
                },
                "target_name": "conflict",
                "horizon_days": 30,
                "label_column": "label",
                "split": {
                    "min_train_periods": 4,
                    "validation_window_periods": 2,
                    "step_periods": 2,
                    "max_splits": 1,
                },
                "models": models,
                "primary_model": primary_model,
                "baseline_model": baseline_model,
                "prediction_threshold": 0.5,
                "seed": 7,
                "calibration_method": "isotonic",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return config_path


def test_backtesting_run_and_replay(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[3]
    pipeline_result = run_country_week_features_pipeline(
        project_root / "configs" / "data_platform" / "pipeline_country_week_features.yaml",
        output_root=tmp_path,
        use_test_snapshots=True,
    )
    dataset_path = pipeline_result.gold_country_week_features_file

    config_path = tmp_path / "country_week_backtest.yaml"
    replay_config_path = tmp_path / "replay_irn.yaml"
    config_payload = yaml.safe_load((project_root / "configs" / "backtesting" / "country_week.yaml").read_text(encoding="utf-8"))
    config_payload["dataset_path"] = str(dataset_path)
    config_payload["primary_model"] = "logit"
    config_payload["split"] = {
        "min_train_periods": 120,
        "validation_window_periods": 30,
        "step_periods": 30,
        "max_splits": 12,
    }
    config_payload["models"] = [
        {"name": "prior_rate", "kind": "prior_rate"},
        {"name": "logit", "kind": "logistic_regression"},
    ]
    config_path.write_text(yaml.safe_dump(config_payload, sort_keys=False), encoding="utf-8")
    replay_config_path.write_text(
        yaml.safe_dump(
            {
                "run_name": "replay_iran",
                "backtest_run_name": "country_week",
                "entity_id": "IRN",
                "max_rows": 12,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    backtest_result = run_backtest(config_path, output_root=tmp_path / "artifacts")
    replay_result = run_replay(replay_config_path, output_root=tmp_path / "artifacts")

    assert backtest_result.predictions_file.exists()
    assert backtest_result.alerts_file.exists()
    assert backtest_result.metrics_file.exists()
    assert backtest_result.report_file.exists()
    assert backtest_result.windows_file.exists()
    assert replay_result.replay_file.exists()

    predictions = pd.read_parquet(backtest_result.predictions_file)
    alerts = pd.read_parquet(backtest_result.alerts_file)
    metrics_payload = json.loads(backtest_result.metrics_file.read_text(encoding="utf-8"))
    report_text = backtest_result.report_file.read_text(encoding="utf-8")
    replay_text = replay_result.replay_file.read_text(encoding="utf-8")

    assert not predictions.empty
    assert not alerts.empty
    assert {"entity_id", "forecast_date", "calibrated_probability", "model_name"}.issubset(predictions.columns)
    assert {"is_alert", "alert_outcome", "alert_episode_id"}.issubset(alerts.columns)
    assert sorted(predictions["model_name"].unique().tolist()) == ["logit", "prior_rate"]
    assert metrics_payload["primary_model"] == "logit"
    assert {"prior_rate", "logit"}.issubset(metrics_payload["models"])
    assert "### prior_rate" in report_text
    assert "### logit" in report_text
    assert "## Baseline Comparison" in report_text
    assert "Top-performing model" in report_text
    assert "probability_distribution.svg" in report_text
    assert "precision_recall.svg" in report_text
    assert "Calibration" in report_text
    assert "alert burden" in report_text.lower()
    assert "# Replay: IRN" in replay_text


def test_backtest_calibrates_using_training_rows_not_held_out_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset_path = _write_minimal_backtest_dataset(tmp_path)
    config_path = _write_backtest_config(
        tmp_path,
        dataset_path=dataset_path,
        run_name="calibration_leak_check",
        models=[{"name": "prior_rate", "kind": "prior_rate"}],
        primary_model="prior_rate",
    )

    fit_lengths: list[int] = []

    def fake_fit_calibrator(method: str, scores, labels):
        fit_lengths.append(len(scores))
        return {"method": method}

    def fake_apply_calibrator(calibrator, scores):
        return pd.Series(scores, dtype=float).to_numpy()

    monkeypatch.setattr("src.backtesting.engine._fit_calibrator", fake_fit_calibrator)
    monkeypatch.setattr("src.backtesting.engine._apply_calibrator", fake_apply_calibrator)

    result = run_backtest(config_path, output_root=tmp_path / "artifacts")

    assert result.predictions_file.exists()
    assert fit_lengths == [4]


def test_checked_in_onset_backtest_config_runs_on_real_country_week_pipeline(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[3]
    pipeline_result = run_country_week_features_pipeline(
        project_root / "configs" / "data_platform" / "pipeline_country_week_features.yaml",
        output_root=tmp_path,
        use_test_snapshots=True,
    )
    config_source = project_root / "configs" / "backtesting" / "country_week_onset_logit.yaml"
    config_payload = yaml.safe_load(config_source.read_text(encoding="utf-8"))
    config_payload["dataset_path"] = str(pipeline_result.gold_country_week_features_file)

    assert config_payload["label_column"] == "label_onset_30d"
    assert config_payload["primary_model"] == "logit"

    config_path = tmp_path / "country_week_onset_logit.yaml"
    config_path.write_text(yaml.safe_dump(config_payload, sort_keys=False), encoding="utf-8")

    result = run_backtest(config_path, output_root=tmp_path / "artifacts")
    metrics_payload = json.loads(result.metrics_file.read_text(encoding="utf-8"))
    predictions = pd.read_parquet(result.predictions_file)

    assert result.predictions_file.exists()
    assert result.report_file.exists()
    assert metrics_payload["primary_model"] == "logit"
    assert {"logit", "prior_rate"}.issubset(metrics_payload["models"])
    assert sorted(predictions["model_name"].unique().tolist()) == ["logit", "prior_rate"]


def test_checked_in_structural_backtest_config_runs_on_real_country_week_pipeline(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[3]
    pipeline_result = run_country_week_features_pipeline(
        project_root / "configs" / "data_platform" / "pipeline_country_week_features.yaml",
        output_root=tmp_path,
        use_test_snapshots=True,
    )
    config_source = project_root / "configs" / "backtesting" / "country_week_onset_structural_90d.yaml"
    config_payload = yaml.safe_load(config_source.read_text(encoding="utf-8"))
    config_payload["dataset_path"] = str(pipeline_result.gold_country_week_features_file)

    assert config_payload["label_column"] == "label_onset_90d"
    assert config_payload["horizon_days"] == 90
    assert config_payload["primary_model"] == "logit"

    config_path = tmp_path / "country_week_onset_structural_90d.yaml"
    config_path.write_text(yaml.safe_dump(config_payload, sort_keys=False), encoding="utf-8")

    result = run_backtest(config_path, output_root=tmp_path / "artifacts")
    metrics_payload = json.loads(result.metrics_file.read_text(encoding="utf-8"))
    predictions = pd.read_parquet(result.predictions_file)

    assert result.predictions_file.exists()
    assert result.report_file.exists()
    assert metrics_payload["primary_model"] == "logit"
    assert {"logit", "prior_rate"}.issubset(metrics_payload["models"])
    assert sorted(predictions["model_name"].unique().tolist()) == ["logit", "prior_rate"]


def test_checked_in_interstate_onset_backtest_config_runs_on_real_country_week_pipeline(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[3]
    pipeline_result = run_country_week_features_pipeline(
        project_root / "configs" / "data_platform" / "pipeline_country_week_features.yaml",
        output_root=tmp_path,
        use_test_snapshots=True,
    )
    interstate_dataset_path = _write_augmented_interstate_dataset(
        pipeline_result.gold_country_week_features_file,
        tmp_path / "country_week_interstate_onset.parquet",
    )
    config_source = project_root / "configs" / "backtesting" / "country_week_interstate_onset_logit.yaml"
    config_payload = yaml.safe_load(config_source.read_text(encoding="utf-8"))
    config_payload["dataset_path"] = str(interstate_dataset_path)
    if "structural_prior" in config_payload:
        structural_prior_file = tmp_path / "country_week_interstate_onset_structural_prior.parquet"
        dataset_frame = pd.read_parquet(interstate_dataset_path)
        pd.DataFrame(
            {
                "entity_id": dataset_frame["country_iso3"],
                "forecast_date": dataset_frame["week_start_date"],
                "calibrated_probability": dataset_frame["label_interstate_onset_90d"].fillna(0).astype(float).map(
                    lambda value: 0.9 if value >= 1 else 0.1
                ),
            }
        ).to_parquet(structural_prior_file, index=False)
        config_payload["structural_prior"]["prediction_file"] = str(structural_prior_file)

    assert config_payload["label_column"] == "label_interstate_onset_30d"
    assert config_payload["primary_model"] == "logit"

    config_path = tmp_path / "country_week_interstate_onset_logit.yaml"
    config_path.write_text(yaml.safe_dump(config_payload, sort_keys=False), encoding="utf-8")

    result = run_backtest(config_path, output_root=tmp_path / "artifacts")
    metrics_payload = json.loads(result.metrics_file.read_text(encoding="utf-8"))
    predictions = pd.read_parquet(result.predictions_file)

    assert result.predictions_file.exists()
    assert result.report_file.exists()
    assert metrics_payload["primary_model"] == "logit"
    assert {"logit", "prior_rate"}.issubset(metrics_payload["models"])
    assert sorted(predictions["model_name"].unique().tolist()) == ["logit", "prior_rate"]


def test_checked_in_interstate_structural_backtest_config_runs_on_real_country_week_pipeline(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[3]
    pipeline_result = run_country_week_features_pipeline(
        project_root / "configs" / "data_platform" / "pipeline_country_week_features.yaml",
        output_root=tmp_path,
        use_test_snapshots=True,
    )
    interstate_dataset_path = _write_augmented_interstate_dataset(
        pipeline_result.gold_country_week_features_file,
        tmp_path / "country_week_interstate_structural.parquet",
    )
    config_source = project_root / "configs" / "backtesting" / "country_week_interstate_onset_structural_90d.yaml"
    config_payload = yaml.safe_load(config_source.read_text(encoding="utf-8"))
    config_payload["dataset_path"] = str(interstate_dataset_path)

    assert config_payload["label_column"] == "label_interstate_onset_90d"
    assert config_payload["horizon_days"] == 90
    assert config_payload["primary_model"] == "logit"

    config_path = tmp_path / "country_week_interstate_onset_structural_90d.yaml"
    config_path.write_text(yaml.safe_dump(config_payload, sort_keys=False), encoding="utf-8")

    result = run_backtest(config_path, output_root=tmp_path / "artifacts")
    metrics_payload = json.loads(result.metrics_file.read_text(encoding="utf-8"))
    predictions = pd.read_parquet(result.predictions_file)

    assert result.predictions_file.exists()
    assert result.report_file.exists()
    assert metrics_payload["primary_model"] == "logit"
    assert {"logit", "prior_rate"}.issubset(metrics_payload["models"])
    assert sorted(predictions["model_name"].unique().tolist()) == ["logit", "prior_rate"]


def test_backtest_rejects_missing_primary_model(tmp_path: Path) -> None:
    dataset_path = _write_minimal_backtest_dataset(tmp_path)
    config_path = _write_backtest_config(
        tmp_path,
        dataset_path=dataset_path,
        run_name="missing_primary_model",
        models=[{"name": "prior_rate", "kind": "prior_rate"}],
        primary_model="logit",
    )

    with pytest.raises(ValueError, match=r"Configured primary model `logit` was not produced"):
        run_backtest(config_path, output_root=tmp_path / "artifacts")


def test_backtest_reports_when_baseline_model_is_unavailable(tmp_path: Path) -> None:
    dataset_path = _write_minimal_backtest_dataset(tmp_path)
    config_path = _write_backtest_config(
        tmp_path,
        dataset_path=dataset_path,
        run_name="no_baseline_model",
        models=[{"name": "logit", "kind": "logistic_regression"}],
        primary_model="logit",
    )

    result = run_backtest(config_path, output_root=tmp_path / "artifacts")
    metrics_payload = json.loads(result.metrics_file.read_text(encoding="utf-8"))
    report_text = result.report_file.read_text(encoding="utf-8")

    assert metrics_payload["primary_model"] == "logit"
    assert metrics_payload["baseline_model"] is None
    assert "Baseline comparison unavailable" in report_text


def test_backtest_rejects_missing_configured_baseline_model(tmp_path: Path) -> None:
    dataset_path = _write_minimal_backtest_dataset(tmp_path)
    config_path = _write_backtest_config(
        tmp_path,
        dataset_path=dataset_path,
        run_name="missing_baseline_model",
        models=[{"name": "logit", "kind": "logistic_regression"}],
        primary_model="logit",
        baseline_model="prior_rate",
    )

    with pytest.raises(ValueError, match="Configured baseline model `prior_rate` was not produced"):
        run_backtest(config_path, output_root=tmp_path / "artifacts")


def test_model_comparison_uses_consistent_brier_delta_sign(tmp_path: Path) -> None:
    model_metrics = {
        "prior_rate": {
            "overall": {
                "precision": 0.25,
                "recall": 0.5,
                "f1": 0.33,
                "pr_auc": 0.4,
                "roc_auc": 0.45,
                "brier_score": 0.6,
            }
        },
        "logit": {
            "overall": {
                "precision": 0.5,
                "recall": 0.75,
                "f1": 0.6,
                "pr_auc": 0.7,
                "roc_auc": 0.8,
                "brier_score": 0.4,
            }
        },
    }
    comparison_summary = summarize_model_comparison(model_metrics, baseline_model="prior_rate")
    report_file = write_backtest_report(
        tmp_path / "summary.md",
        run_name="comparison_sign",
        target_name="conflict",
        primary_model="logit",
        baseline_model="prior_rate",
        model_metrics=model_metrics,
        comparison_summary=comparison_summary,
        alert_metrics={
            "new_alert_count": 1,
            "true_alert_count": 1,
            "false_alert_count": 0,
            "new_label_episode_count": 1,
            "first_alert_lead_days_mean": 3.0,
            "first_alert_lead_days_median": 3.0,
            "false_alert_burden": 0,
        },
        calibration_method="isotonic",
        plot_references={
            "probability_distribution": "probability_distribution.svg",
            "precision_recall": "precision_recall.svg",
        },
    )
    report_text = report_file.read_text(encoding="utf-8")

    assert comparison_summary["baseline_deltas"][0]["delta_brier_score"] == pytest.approx(-0.2)
    assert "negative is better" in report_text.lower()


def test_replay_report_identifies_the_model_being_replayed(tmp_path: Path) -> None:
    backtest_run_dir = tmp_path / "artifacts" / "run" / "ambiguous_backtest"
    backtest_run_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "entity_id": ["IRN", "IRN"],
            "entity_name": ["Iran", "Iran"],
            "forecast_date": [pd.Timestamp("2025-01-08"), pd.Timestamp("2025-01-01")],
            "model_name": ["logit", "logit"],
            "calibrated_probability": [0.71, 0.63],
            "label": [1, 0],
        }
    ).to_parquet(backtest_run_dir / "predictions.parquet", index=False)
    pd.DataFrame(
        {
            "entity_id": ["IRN", "IRN"],
            "forecast_date": [pd.Timestamp("2025-01-08"), pd.Timestamp("2025-01-01")],
            "is_alert": [True, False],
            "alert_outcome": ["true_alert", None],
        }
    ).to_parquet(backtest_run_dir / "alerts.parquet", index=False)
    (backtest_run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "primary_model": "logit",
                "baseline_model": "prior_rate",
                "comparison": {"top_model": {"model_name": "prior_rate"}},
            }
        ),
        encoding="utf-8",
    )

    replay_config_path = tmp_path / "replay.yaml"
    replay_config_path.write_text(
        yaml.safe_dump(
            {
                "run_name": "replay_ambiguous",
                "backtest_run_name": "ambiguous_backtest",
                "entity_id": "IRN",
                "max_rows": 12,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    replay_result = run_replay(replay_config_path, output_root=tmp_path / "artifacts")
    replay_text = replay_result.replay_file.read_text(encoding="utf-8")

    assert "Model: `logit`" in replay_text


def test_replay_uses_configured_model_override(tmp_path: Path) -> None:
    backtest_run_dir = tmp_path / "artifacts" / "run" / "override_backtest"
    backtest_run_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "entity_id": ["IRN", "IRN"],
            "entity_name": ["Iran", "Iran"],
            "forecast_date": [pd.Timestamp("2025-01-08"), pd.Timestamp("2025-01-01")],
            "model_name": ["prior_rate", "prior_rate"],
            "calibrated_probability": [0.41, 0.37],
            "label": [1, 0],
        }
    ).to_parquet(backtest_run_dir / "predictions.parquet", index=False)
    pd.DataFrame(
        {
            "entity_id": ["IRN", "IRN"],
            "forecast_date": [pd.Timestamp("2025-01-08"), pd.Timestamp("2025-01-01")],
            "is_alert": [False, False],
            "alert_outcome": [None, None],
        }
    ).to_parquet(backtest_run_dir / "alerts.parquet", index=False)
    (backtest_run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "primary_model": "logit",
                "baseline_model": "prior_rate",
                "comparison": {"top_model": {"model_name": "prior_rate"}},
            }
        ),
        encoding="utf-8",
    )

    replay_config_path = tmp_path / "replay_override.yaml"
    replay_config_path.write_text(
        yaml.safe_dump(
            {
                "run_name": "replay_override",
                "backtest_run_name": "override_backtest",
                "entity_id": "IRN",
                "model_name": "prior_rate",
                "max_rows": 12,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    replay_result = run_replay(replay_config_path, output_root=tmp_path / "artifacts")
    replay_text = replay_result.replay_file.read_text(encoding="utf-8")

    assert "Model: `prior_rate`" in replay_text
