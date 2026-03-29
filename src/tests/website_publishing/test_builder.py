from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from src.website_publishing.builder import build_site_snapshot
from src.website_publishing.cli import run_publish


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _prediction_rows(model_name: str = "logit") -> list[dict[str, object]]:
    return [
        {
            "country_iso3": "LBN",
            "country_name": "Lebanon",
            "region_name": "Middle East",
            "forecast_date": "2026-03-23",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
            "calibrated_probability": 0.84,
            "model_name": model_name,
            "model_version": "country_week_logit_30d",
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "calibration_run_name": f"country_week_{model_name}",
            "calibration_model_name": model_name,
            "calibration_training_run_name": "train_country_week_logit_30d",
            "training_window_id": "2015-01-05_2026-02-23",
            "feature_snapshot_hash": "hash-lbn-1",
            "top_positive_drivers": json.dumps(
                [
                    {"feature": "acled_event_count_28d", "contribution": 1.2},
                    {"feature": "gdelt_event_count_7d", "contribution": 0.6},
                ]
            ),
        },
        {
            "country_iso3": "LBN",
            "country_name": "Lebanon",
            "region_name": "Middle East",
            "forecast_date": "2026-03-16",
            "snapshot_ts_utc": "2026-03-21T06:00:00Z",
            "calibrated_probability": 0.78,
            "model_name": model_name,
            "model_version": "country_week_logit_30d",
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "calibration_run_name": f"country_week_{model_name}",
            "calibration_model_name": model_name,
            "calibration_training_run_name": "train_country_week_logit_30d",
            "training_window_id": "2015-01-05_2026-02-16",
            "feature_snapshot_hash": "hash-lbn-0",
            "top_positive_drivers": json.dumps(
                [
                    {"feature": "acled_event_count_28d", "contribution": 1.1},
                    {"feature": "market_oil_price_usd_per_barrel", "contribution": 0.3},
                ]
            ),
        },
        {
            "country_iso3": "ISR",
            "country_name": "Israel",
            "region_name": "Middle East",
            "forecast_date": "2026-03-23",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
            "calibrated_probability": 0.79,
            "model_name": model_name,
            "model_version": "country_week_logit_30d",
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "calibration_run_name": f"country_week_{model_name}",
            "calibration_model_name": model_name,
            "calibration_training_run_name": "train_country_week_logit_30d",
            "training_window_id": "2015-01-05_2026-02-23",
            "feature_snapshot_hash": "hash-isr-1",
            "top_positive_drivers": json.dumps(
                [
                    {"feature": "gdelt_num_mentions_7d", "contribution": 0.8},
                    {"feature": "security_military_expenditure_pct_gdp", "contribution": 0.5},
                ]
            ),
        },
        {
            "country_iso3": "ISR",
            "country_name": "Israel",
            "region_name": "Middle East",
            "forecast_date": "2026-03-16",
            "snapshot_ts_utc": "2026-03-21T06:00:00Z",
            "calibrated_probability": 0.74,
            "model_name": model_name,
            "model_version": "country_week_logit_30d",
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "calibration_run_name": f"country_week_{model_name}",
            "calibration_model_name": model_name,
            "calibration_training_run_name": "train_country_week_logit_30d",
            "training_window_id": "2015-01-05_2026-02-16",
            "feature_snapshot_hash": "hash-isr-0",
            "top_positive_drivers": json.dumps(
                [
                    {"feature": "gdelt_num_mentions_7d", "contribution": 0.6},
                    {"feature": "shipping_lsci_index", "contribution": 0.4},
                ]
            ),
        },
    ]


def _targeted_prediction_rows(
    *,
    target_name: str,
    model_version: str,
    calibration_run_name: str,
    calibration_training_run_name: str,
    model_name: str = "logit",
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in _prediction_rows(model_name):
        targeted_row = dict(row)
        targeted_row["target_name"] = target_name
        targeted_row["model_version"] = model_version
        targeted_row["calibration_run_name"] = calibration_run_name
        targeted_row["calibration_training_run_name"] = calibration_training_run_name
        rows.append(targeted_row)
    return rows


def _tied_prediction_rows() -> list[dict[str, object]]:
    return [
        {
            "country_iso3": "ALP",
            "country_name": "Alpha",
            "region_name": "Test Region",
            "forecast_date": "2026-03-23",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
            "calibrated_probability": 0.000449185850645705,
            "raw_score": 0.12,
            "model_name": "logit",
            "model_version": "country_week_logit_30d",
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "calibration_run_name": "country_week_logit",
            "calibration_model_name": "logit",
            "calibration_training_run_name": "train_country_week_logit_30d",
            "training_window_id": "2015-01-05_2026-02-23",
            "feature_snapshot_hash": "hash-alp-1",
            "top_positive_drivers": json.dumps([{"feature": "feature_alpha", "contribution": 0.2}]),
        },
        {
            "country_iso3": "ZUL",
            "country_name": "Zulu",
            "region_name": "Test Region",
            "forecast_date": "2026-03-23",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
            "calibrated_probability": 0.000449185850645705,
            "raw_score": 0.91,
            "model_name": "logit",
            "model_version": "country_week_logit_30d",
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "calibration_run_name": "country_week_logit",
            "calibration_model_name": "logit",
            "calibration_training_run_name": "train_country_week_logit_30d",
            "training_window_id": "2015-01-05_2026-02-23",
            "feature_snapshot_hash": "hash-zul-1",
            "top_positive_drivers": json.dumps([{"feature": "feature_zulu", "contribution": 0.9}]),
        },
        {
            "country_iso3": "MID",
            "country_name": "Middle",
            "region_name": "Test Region",
            "forecast_date": "2026-03-23",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
            "calibrated_probability": 0.0003,
            "raw_score": 0.05,
            "model_name": "logit",
            "model_version": "country_week_logit_30d",
            "target_name": "country_week_escalation_30d",
            "horizon_days": 30,
            "calibration_run_name": "country_week_logit",
            "calibration_model_name": "logit",
            "calibration_training_run_name": "train_country_week_logit_30d",
            "training_window_id": "2015-01-05_2026-02-23",
            "feature_snapshot_hash": "hash-mid-1",
            "top_positive_drivers": json.dumps([{"feature": "feature_mid", "contribution": 0.1}]),
        },
    ]


def _report_input_rows() -> list[dict[str, object]]:
    return [
        {
            "report_id": "report-lbn-latest",
            "report_slug": "lbn-latest",
            "report_title": "Lebanon Weekly Risk Brief",
            "country_iso3": "LBN",
            "country_name": "Lebanon",
            "region_name": "Middle East",
            "report_date": "2026-03-29",
            "as_of_date": "2026-03-29",
            "forecast_horizon_days": 30,
            "forecast_target": "label_escalation_30d",
            "forecast_probability": 0.84,
            "risk_level": "high",
            "freshness_days": 2,
            "summary": "Lebanon remains the lead escalation case in the weekly snapshot.",
            "predicted_conflict_label": "Lebanon / Israel",
            "predicted_conflict_countries": json.dumps(
                [
                    {"iso3": "LBN", "country_name": "Lebanon"},
                    {"iso3": "ISR", "country_name": "Israel"},
                ]
            ),
            "reason_source": "report_inputs",
            "chronology": json.dumps(
                [
                    "Week of 2026-03-23: cross-border pressure remained elevated.",
                    "Trailing 28-day ACLED events: 12.",
                ]
            ),
            "top_drivers": json.dumps(["ACLED events (28d): 12", "GDELT events (7d): 9"]),
            "top_drivers_json": json.dumps(["ACLED events (28d): 12", "GDELT events (7d): 9"]),
            "source_snapshot_hash": "report-lbn-hash",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
        },
        {
            "report_id": "report-isr-latest",
            "report_slug": "isr-latest",
            "report_title": "Israel Weekly Risk Brief",
            "country_iso3": "ISR",
            "country_name": "Israel",
            "region_name": "Middle East",
            "report_date": "2026-03-29",
            "as_of_date": "2026-03-29",
            "forecast_horizon_days": 30,
            "forecast_target": "label_escalation_30d",
            "forecast_probability": 0.79,
            "risk_level": "high",
            "freshness_days": 2,
            "summary": "Israel remains tightly coupled to the lead theater.",
            "predicted_conflict_label": "Lebanon / Israel",
            "predicted_conflict_countries": json.dumps(
                [
                    {"iso3": "LBN", "country_name": "Lebanon"},
                    {"iso3": "ISR", "country_name": "Israel"},
                ]
            ),
            "reason_source": "report_inputs",
            "chronology": json.dumps(
                [
                    "Week of 2026-03-23: deterrence language hardened.",
                    "Trailing 28-day ACLED events: 7.",
                ]
            ),
            "top_drivers": json.dumps(["GDELT mentions (7d): 16", "Shipping LSCI: 92"]),
            "top_drivers_json": json.dumps(["GDELT mentions (7d): 16", "Shipping LSCI: 92"]),
            "source_snapshot_hash": "report-isr-hash",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
        },
    ]


def _training_manifest(
    *,
    run_name: str = "train_country_week_logit_30d",
    primary_model: str = "logit",
    target_name: str = "country_week_escalation_30d",
    horizon_days: int = 30,
) -> dict[str, object]:
    return {
        "run_name": run_name,
        "target_name": target_name,
        "horizon_days": horizon_days,
        "primary_model": primary_model,
        "training_window_id": "2015-01-05_2026-02-23",
        "feature_columns": ["acled_event_count_28d", "gdelt_event_count_7d"],
    }


def _training_metrics(model_name: str = "logit") -> dict[str, object]:
    return {
        "primary_model": model_name,
        "models": {
            model_name: {
                "overall": {
                    "precision": 0.3,
                    "recall": 0.22,
                    "f1": 0.25,
                    "pr_auc": 0.41,
                    "roc_auc": 0.81,
                    "brier_score": 0.14,
                    "top_k_risk_hit_rate": 0.3,
                }
            },
            "prior_rate": {
                "overall": {
                    "precision": 0.2,
                    "recall": 0.18,
                    "f1": 0.19,
                    "pr_auc": 0.34,
                    "roc_auc": 0.73,
                    "brier_score": 0.18,
                    "top_k_risk_hit_rate": 0.2,
                }
            }
        },
    }


def _calibration_metrics(
    model_name: str = "logit",
    *,
    run_name: str | None = None,
    training_run_name: str = "train_country_week_logit_30d",
) -> dict[str, object]:
    return {
        "run_name": run_name or f"country_week_{model_name}",
        "method": "isotonic",
        "model_name": model_name,
        "training_run_name": training_run_name,
        "training_window_id": "2015-01-05_2026-02-23",
        "metrics": {
            "roc_auc": 0.81,
            "brier_score": 0.14,
        },
    }


def _backtest_metrics(model_name: str = "logit", *, top_model_name: str = "prior_rate") -> dict[str, object]:
    return {
        "primary_model": model_name,
        "baseline_model": "prior_rate",
        "comparison": {
            "top_model": {"model_name": top_model_name},
            "baseline_deltas": [
                {
                    "model_name": model_name,
                    "delta_pr_auc": -0.01,
                    "delta_roc_auc": 0.03,
                    "delta_f1": 0.02,
                    "delta_brier_score": -0.04,
                }
            ],
        },
        "alerts": {
            "publish_threshold": 0.82,
            "alert_threshold": 0.76,
            "false_alert_burden": 1,
            "new_alert_count": 2,
            "true_alert_count": 1,
            "false_alert_count": 1,
            "episode_recall": 0.44,
            "false_alerts_per_true_alert": 1.0,
            "recall_at_5": 0.31,
            "recall_at_10": 0.52,
            "no_clear_leader_rate": 0.14,
        },
        "calibration": {"method": "isotonic"},
    }


def _write_publisher_inputs(tmp_path: Path, *, preferred_exists: bool = True) -> dict[str, Path]:
    preferred_prediction_file = tmp_path / "artifacts" / "forecasting" / "predict" / "country_week_logit" / "predictions.parquet"
    baseline_prediction_file = tmp_path / "artifacts" / "forecasting" / "predict" / "country_week_default" / "predictions.parquet"
    training_manifest_file = tmp_path / "artifacts" / "forecasting" / "train" / "country_week_logit_30d" / "manifest.json"
    training_metrics_file = tmp_path / "artifacts" / "forecasting" / "train" / "country_week_logit_30d" / "metrics.json"
    calibration_metrics_file = tmp_path / "artifacts" / "forecasting" / "calibration" / "country_week_logit" / "calibration_metrics.json"
    backtest_metrics_file = tmp_path / "artifacts" / "backtesting" / "run" / "country_week_logit" / "metrics.json"
    structural_training_manifest_file = (
        tmp_path / "artifacts" / "forecasting" / "train" / "country_week_onset_structural_90d" / "manifest.json"
    )
    structural_calibration_metrics_file = (
        tmp_path / "artifacts" / "forecasting" / "calibration" / "country_week_onset_structural_90d" / "calibration_metrics.json"
    )
    structural_backtest_metrics_file = (
        tmp_path / "artifacts" / "backtesting" / "run" / "country_week_onset_structural_90d" / "metrics.json"
    )
    baseline_training_manifest_file = tmp_path / "artifacts" / "forecasting" / "train" / "country_week_30d" / "manifest.json"
    baseline_training_metrics_file = tmp_path / "artifacts" / "forecasting" / "train" / "country_week_30d" / "metrics.json"
    baseline_calibration_metrics_file = tmp_path / "artifacts" / "forecasting" / "calibration" / "country_week_default" / "calibration_metrics.json"
    baseline_backtest_metrics_file = tmp_path / "artifacts" / "backtesting" / "run" / "country_week" / "metrics.json"
    report_inputs_file = tmp_path / "data" / "gold" / "report_inputs" / "report_inputs.parquet"

    baseline_prediction_file.parent.mkdir(parents=True, exist_ok=True)
    report_inputs_file.parent.mkdir(parents=True, exist_ok=True)
    training_manifest_file.parent.mkdir(parents=True, exist_ok=True)
    training_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    calibration_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    backtest_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    structural_training_manifest_file.parent.mkdir(parents=True, exist_ok=True)
    structural_calibration_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    structural_backtest_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_training_manifest_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_training_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_calibration_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_backtest_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    if preferred_exists:
        preferred_prediction_file.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(_prediction_rows()).to_parquet(preferred_prediction_file, index=False)
    pd.DataFrame(_prediction_rows("prior_rate")).to_parquet(baseline_prediction_file, index=False)
    pd.DataFrame(_report_input_rows()).to_parquet(report_inputs_file, index=False)

    _write_json(training_manifest_file, _training_manifest())
    _write_json(training_metrics_file, _training_metrics())
    _write_json(calibration_metrics_file, _calibration_metrics())
    _write_json(backtest_metrics_file, _backtest_metrics())
    _write_json(
        structural_training_manifest_file,
        _training_manifest(
            run_name="train_country_week_onset_structural_90d",
            primary_model="logit",
            target_name="country_week_onset_90d",
            horizon_days=90,
        ),
    )
    _write_json(
        structural_calibration_metrics_file,
        _calibration_metrics(
            "logit",
            run_name="country_week_onset_structural_90d",
            training_run_name="train_country_week_onset_structural_90d",
        ),
    )
    _write_json(structural_backtest_metrics_file, _backtest_metrics())
    _write_json(
        baseline_training_manifest_file,
        _training_manifest(run_name="train_country_week_30d", primary_model="prior_rate"),
    )
    _write_json(baseline_training_metrics_file, _training_metrics("prior_rate"))
    _write_json(baseline_calibration_metrics_file, _calibration_metrics("prior_rate"))
    _write_json(baseline_backtest_metrics_file, _backtest_metrics("prior_rate"))

    return {
        "preferred_prediction_file": preferred_prediction_file,
        "baseline_prediction_file": baseline_prediction_file,
        "training_manifest_file": training_manifest_file,
        "training_metrics_file": training_metrics_file,
        "calibration_metrics_file": calibration_metrics_file,
        "backtest_metrics_file": backtest_metrics_file,
        "structural_training_manifest_file": structural_training_manifest_file,
        "structural_calibration_metrics_file": structural_calibration_metrics_file,
        "structural_backtest_metrics_file": structural_backtest_metrics_file,
        "baseline_training_manifest_file": baseline_training_manifest_file,
        "baseline_training_metrics_file": baseline_training_metrics_file,
        "baseline_calibration_metrics_file": baseline_calibration_metrics_file,
        "baseline_backtest_metrics_file": baseline_backtest_metrics_file,
        "report_inputs_file": report_inputs_file,
    }


def _write_config(tmp_path: Path, inputs: dict[str, Path]) -> Path:
    config_path = tmp_path / "configs" / "website_publishing" / "site_snapshot.yaml"
    _write_yaml(
        config_path,
        {
            "run_name": "site_snapshot",
            "preferred_prediction_file": str(inputs["preferred_prediction_file"]),
            "baseline_prediction_file": str(inputs["baseline_prediction_file"]),
            "training_manifest_file": str(inputs["training_manifest_file"]),
            "training_metrics_file": str(inputs["training_metrics_file"]),
            "calibration_metrics_file": str(inputs["calibration_metrics_file"]),
            "backtest_metrics_file": str(inputs["backtest_metrics_file"]),
            "structural_training_manifest_file": str(inputs["structural_training_manifest_file"]),
            "structural_calibration_metrics_file": str(inputs["structural_calibration_metrics_file"]),
            "structural_backtest_metrics_file": str(inputs["structural_backtest_metrics_file"]),
            "baseline_training_manifest_file": str(inputs["baseline_training_manifest_file"]),
            "baseline_training_metrics_file": str(inputs["baseline_training_metrics_file"]),
            "baseline_calibration_metrics_file": str(inputs["baseline_calibration_metrics_file"]),
            "baseline_backtest_metrics_file": str(inputs["baseline_backtest_metrics_file"]),
            "report_inputs_file": str(inputs["report_inputs_file"]),
            "output_dir": str(tmp_path / "artifacts" / "website_publishing" / "site_snapshot" / "latest"),
            "published_at": "2026-03-28T12:00:00Z",
            "fresh_window_days": 10,
            "stale_window_days": 21,
            "publish_top_n": 10,
            "alert_threshold": 0.7,
            "warning_threshold": 0.5,
            "operating_threshold": 0.6,
        },
    )
    return config_path


def test_build_site_snapshot_writes_bundle_and_country_files(tmp_path: Path) -> None:
    inputs = _write_publisher_inputs(tmp_path)
    output_dir = tmp_path / "artifacts" / "website_publishing" / "site_snapshot" / "latest"

    result = build_site_snapshot(
        run_name="site_snapshot",
        preferred_prediction_file=inputs["preferred_prediction_file"],
        baseline_prediction_file=inputs["baseline_prediction_file"],
        training_manifest_file=inputs["training_manifest_file"],
        training_metrics_file=inputs["training_metrics_file"],
        calibration_metrics_file=inputs["calibration_metrics_file"],
        backtest_metrics_file=inputs["backtest_metrics_file"],
        baseline_training_manifest_file=inputs["baseline_training_manifest_file"],
        baseline_training_metrics_file=inputs["baseline_training_metrics_file"],
        baseline_calibration_metrics_file=inputs["baseline_calibration_metrics_file"],
        baseline_backtest_metrics_file=inputs["baseline_backtest_metrics_file"],
        report_inputs_file=inputs["report_inputs_file"],
        output_dir=output_dir,
        published_at="2026-03-28T12:00:00Z",
        fresh_window_days=10,
        stale_window_days=21,
        publish_top_n=10,
        alert_threshold=0.7,
        warning_threshold=0.5,
        operating_threshold=0.6,
    )

    assert result.manifest_file.exists()
    assert result.forecast_snapshot_file.exists()
    assert result.backtest_summary_file.exists()
    assert result.model_card_file.exists()
    assert result.status_file.exists()
    assert result.country_dir.exists()

    manifest_payload = json.loads(result.manifest_file.read_text(encoding="utf-8"))
    forecast_snapshot_payload = json.loads(result.forecast_snapshot_file.read_text(encoding="utf-8"))
    country_payload = json.loads((result.country_dir / "lbn.json").read_text(encoding="utf-8"))
    model_card_payload = json.loads(result.model_card_file.read_text(encoding="utf-8"))
    status_payload = json.loads(result.status_file.read_text(encoding="utf-8"))

    assert manifest_payload["baseline_used"] is False
    assert manifest_payload["top_country_iso3"] == "LBN"
    assert manifest_payload["predicted_conflict"]["label"] == "Lebanon / Israel"
    assert forecast_snapshot_payload["countries"][0]["iso3"] == "LBN"
    assert forecast_snapshot_payload["countries"][0]["delta"] == 0.06
    assert forecast_snapshot_payload["predicted_conflict"]["countries"][1]["iso3"] == "ISR"
    assert country_payload["report_slug"] == "lbn-latest"
    assert country_payload["summary"] == "Lebanon remains the lead escalation case in the weekly snapshot."
    assert country_payload["chronology"][0].startswith("Week of 2026-03-23")
    assert model_card_payload["threshold_policy"]["publish_top_n"] == 10
    assert model_card_payload["metrics"]["roc_auc"] == 0.81
    assert status_payload["freshness_tier"] == "fresh"
    assert status_payload["predicted_conflict"]["reason_source"] == "report_inputs"


def test_build_site_snapshot_uses_baseline_fallback_when_preferred_prediction_is_missing(tmp_path: Path) -> None:
    inputs = _write_publisher_inputs(tmp_path, preferred_exists=False)

    result = build_site_snapshot(
        run_name="site_snapshot",
        preferred_prediction_file=inputs["preferred_prediction_file"],
        baseline_prediction_file=inputs["baseline_prediction_file"],
        training_manifest_file=inputs["training_manifest_file"],
        training_metrics_file=inputs["training_metrics_file"],
        calibration_metrics_file=inputs["calibration_metrics_file"],
        backtest_metrics_file=inputs["backtest_metrics_file"],
        baseline_training_manifest_file=inputs["baseline_training_manifest_file"],
        baseline_training_metrics_file=inputs["baseline_training_metrics_file"],
        baseline_calibration_metrics_file=inputs["baseline_calibration_metrics_file"],
        baseline_backtest_metrics_file=inputs["baseline_backtest_metrics_file"],
        report_inputs_file=inputs["report_inputs_file"],
        output_dir=tmp_path / "artifacts" / "website_publishing" / "site_snapshot" / "latest",
        published_at="2026-03-28T12:00:00Z",
        fresh_window_days=10,
        stale_window_days=21,
        publish_top_n=10,
        alert_threshold=0.7,
        warning_threshold=0.5,
        operating_threshold=0.6,
    )

    manifest_payload = json.loads(result.manifest_file.read_text(encoding="utf-8"))
    model_card_payload = json.loads(result.model_card_file.read_text(encoding="utf-8"))

    assert manifest_payload["baseline_used"] is True
    assert model_card_payload["baseline_used"] is True


def test_build_site_snapshot_uses_baseline_fallback_when_preferred_prediction_is_invalid(tmp_path: Path) -> None:
    inputs = _write_publisher_inputs(tmp_path)
    pd.DataFrame([{"country_iso3": "BROKEN"}]).to_parquet(inputs["preferred_prediction_file"], index=False)

    result = build_site_snapshot(
        run_name="site_snapshot",
        preferred_prediction_file=inputs["preferred_prediction_file"],
        baseline_prediction_file=inputs["baseline_prediction_file"],
        training_manifest_file=inputs["training_manifest_file"],
        training_metrics_file=inputs["training_metrics_file"],
        calibration_metrics_file=inputs["calibration_metrics_file"],
        backtest_metrics_file=inputs["backtest_metrics_file"],
        baseline_training_manifest_file=inputs["baseline_training_manifest_file"],
        baseline_training_metrics_file=inputs["baseline_training_metrics_file"],
        baseline_calibration_metrics_file=inputs["baseline_calibration_metrics_file"],
        baseline_backtest_metrics_file=inputs["baseline_backtest_metrics_file"],
        report_inputs_file=inputs["report_inputs_file"],
        output_dir=tmp_path / "artifacts" / "website_publishing" / "site_snapshot" / "latest",
        published_at="2026-03-28T12:00:00Z",
        fresh_window_days=10,
        stale_window_days=21,
        publish_top_n=10,
        alert_threshold=0.7,
        warning_threshold=0.5,
        operating_threshold=0.6,
    )

    manifest_payload = json.loads(result.manifest_file.read_text(encoding="utf-8"))
    status_payload = json.loads(result.status_file.read_text(encoding="utf-8"))
    model_card_payload = json.loads(result.model_card_file.read_text(encoding="utf-8"))

    assert manifest_payload["baseline_used"] is True
    assert status_payload["baseline_used"] is True
    assert status_payload["prediction_file"].replace("\\", "/").endswith("country_week_default/predictions.parquet")
    assert model_card_payload["model_name"] == "prior_rate"
    assert model_card_payload["provenance"]["escalation"]["training"]["run_name"] == "train_country_week_30d"


def test_build_site_snapshot_uses_raw_score_before_alphabetical_fallback_when_scores_tie(tmp_path: Path) -> None:
    inputs = _write_publisher_inputs(tmp_path, preferred_exists=False)
    preferred_prediction_file = tmp_path / "artifacts" / "forecasting" / "predict" / "country_week_logit" / "predictions.parquet"
    preferred_prediction_file.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(_tied_prediction_rows()).to_parquet(preferred_prediction_file, index=False)

    result = build_site_snapshot(
        run_name="site_snapshot",
        preferred_prediction_file=preferred_prediction_file,
        baseline_prediction_file=inputs["baseline_prediction_file"],
        training_manifest_file=inputs["training_manifest_file"],
        training_metrics_file=inputs["training_metrics_file"],
        calibration_metrics_file=inputs["calibration_metrics_file"],
        backtest_metrics_file=inputs["backtest_metrics_file"],
        baseline_training_manifest_file=inputs["baseline_training_manifest_file"],
        baseline_training_metrics_file=inputs["baseline_training_metrics_file"],
        baseline_calibration_metrics_file=inputs["baseline_calibration_metrics_file"],
        baseline_backtest_metrics_file=inputs["baseline_backtest_metrics_file"],
        report_inputs_file=inputs["report_inputs_file"],
        output_dir=tmp_path / "artifacts" / "website_publishing" / "site_snapshot" / "latest",
        published_at="2026-03-28T12:00:00Z",
        fresh_window_days=10,
        stale_window_days=21,
        publish_top_n=10,
        alert_threshold=0.7,
        warning_threshold=0.5,
        operating_threshold=0.6,
    )

    forecast_snapshot_payload = json.loads(result.forecast_snapshot_file.read_text(encoding="utf-8"))
    status_payload = json.loads(result.status_file.read_text(encoding="utf-8"))

    assert forecast_snapshot_payload["countries"][0]["iso3"] == "ZUL"
    assert forecast_snapshot_payload["countries"][0]["score"] == 0.0004
    assert forecast_snapshot_payload["countries"][0]["rank"] == 1
    assert status_payload["lead_country_iso3"] == "ZUL"
    assert status_payload["lead_tie_count"] == 2


def test_build_site_snapshot_uses_baseline_fallback_when_preferred_prediction_has_invalid_values(tmp_path: Path) -> None:
    inputs = _write_publisher_inputs(tmp_path, preferred_exists=False)
    preferred_prediction_file = tmp_path / "artifacts" / "forecasting" / "predict" / "country_week_logit" / "predictions.parquet"
    preferred_prediction_file.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "country_iso3": "BAD",
                "country_name": "Brokenland",
                "region_name": "Nowhere",
                "forecast_date": "not-a-date",
                "snapshot_ts_utc": "2026-03-28T06:00:00Z",
                "calibrated_probability": "not-a-number",
                "raw_score": 0.4,
                "model_name": "logit",
                "model_version": "country_week_logit_30d",
                "target_name": "country_week_escalation_30d",
                "horizon_days": 30,
            }
        ]
    ).to_parquet(preferred_prediction_file, index=False)

    result = build_site_snapshot(
        run_name="site_snapshot",
        preferred_prediction_file=preferred_prediction_file,
        baseline_prediction_file=inputs["baseline_prediction_file"],
        training_manifest_file=inputs["training_manifest_file"],
        training_metrics_file=inputs["training_metrics_file"],
        calibration_metrics_file=inputs["calibration_metrics_file"],
        backtest_metrics_file=inputs["backtest_metrics_file"],
        baseline_training_manifest_file=inputs["baseline_training_manifest_file"],
        baseline_training_metrics_file=inputs["baseline_training_metrics_file"],
        baseline_calibration_metrics_file=inputs["baseline_calibration_metrics_file"],
        baseline_backtest_metrics_file=inputs["baseline_backtest_metrics_file"],
        report_inputs_file=inputs["report_inputs_file"],
        output_dir=tmp_path / "artifacts" / "website_publishing" / "site_snapshot" / "latest",
        published_at="2026-03-28T12:00:00Z",
        fresh_window_days=10,
        stale_window_days=21,
        publish_top_n=10,
        alert_threshold=0.7,
        warning_threshold=0.5,
        operating_threshold=0.6,
    )

    status_payload = json.loads(result.status_file.read_text(encoding="utf-8"))
    assert status_payload["baseline_used"] is True


def test_build_site_snapshot_publishes_onset_first_contract_with_secondary_escalation_provenance(tmp_path: Path) -> None:
    inputs = _write_publisher_inputs(tmp_path)
    onset_prediction_file = tmp_path / "artifacts" / "forecasting" / "predict" / "country_week_onset_logit" / "predictions.parquet"
    onset_training_manifest_file = tmp_path / "artifacts" / "forecasting" / "train" / "country_week_onset_logit_30d" / "manifest.json"
    onset_training_metrics_file = tmp_path / "artifacts" / "forecasting" / "train" / "country_week_onset_logit_30d" / "metrics.json"
    onset_calibration_metrics_file = tmp_path / "artifacts" / "forecasting" / "calibration" / "country_week_onset_logit" / "calibration_metrics.json"
    onset_backtest_metrics_file = tmp_path / "artifacts" / "backtesting" / "run" / "country_week_onset_logit" / "metrics.json"

    onset_prediction_file.parent.mkdir(parents=True, exist_ok=True)
    onset_training_manifest_file.parent.mkdir(parents=True, exist_ok=True)
    onset_training_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    onset_calibration_metrics_file.parent.mkdir(parents=True, exist_ok=True)
    onset_backtest_metrics_file.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        _targeted_prediction_rows(
            target_name="country_week_onset_30d",
            model_version="country_week_onset_logit_30d",
            calibration_run_name="country_week_onset_logit",
            calibration_training_run_name="train_country_week_onset_logit_30d",
        )
    ).to_parquet(onset_prediction_file, index=False)
    _write_json(
        onset_training_manifest_file,
        _training_manifest(
            run_name="train_country_week_onset_logit_30d",
            primary_model="logit",
            target_name="country_week_onset_30d",
        ),
    )
    _write_json(onset_training_metrics_file, _training_metrics())
    _write_json(onset_calibration_metrics_file, _calibration_metrics())
    _write_json(onset_backtest_metrics_file, _backtest_metrics(top_model_name="logit"))

    result = build_site_snapshot(
        run_name="site_snapshot",
        preferred_prediction_file=onset_prediction_file,
        baseline_prediction_file=inputs["baseline_prediction_file"],
        training_manifest_file=onset_training_manifest_file,
        training_metrics_file=onset_training_metrics_file,
        calibration_metrics_file=onset_calibration_metrics_file,
        backtest_metrics_file=onset_backtest_metrics_file,
        secondary_prediction_file=inputs["preferred_prediction_file"],
        secondary_training_manifest_file=inputs["training_manifest_file"],
        secondary_training_metrics_file=inputs["training_metrics_file"],
        secondary_calibration_metrics_file=inputs["calibration_metrics_file"],
        secondary_backtest_metrics_file=inputs["backtest_metrics_file"],
        structural_training_manifest_file=inputs["structural_training_manifest_file"],
        structural_calibration_metrics_file=inputs["structural_calibration_metrics_file"],
        structural_backtest_metrics_file=inputs["structural_backtest_metrics_file"],
        baseline_training_manifest_file=inputs["baseline_training_manifest_file"],
        baseline_training_metrics_file=inputs["baseline_training_metrics_file"],
        baseline_calibration_metrics_file=inputs["baseline_calibration_metrics_file"],
        baseline_backtest_metrics_file=inputs["baseline_backtest_metrics_file"],
        report_inputs_file=inputs["report_inputs_file"],
        output_dir=tmp_path / "artifacts" / "website_publishing" / "site_snapshot" / "latest",
        published_at="2026-03-28T12:00:00Z",
        fresh_window_days=10,
        stale_window_days=21,
        publish_top_n=10,
        alert_threshold=0.7,
        warning_threshold=0.5,
        operating_threshold=0.6,
    )

    manifest_payload = json.loads(result.manifest_file.read_text(encoding="utf-8"))
    forecast_snapshot_payload = json.loads(result.forecast_snapshot_file.read_text(encoding="utf-8"))
    model_card_payload = json.loads(result.model_card_file.read_text(encoding="utf-8"))
    status_payload = json.loads(result.status_file.read_text(encoding="utf-8"))

    assert manifest_payload["primary_target"] == "onset"
    assert manifest_payload["alert_type"] == "Onset Watch"
    assert manifest_payload["no_clear_leader"] is False
    assert manifest_payload["provenance"]["onset"]["training"]["run_name"] == "train_country_week_onset_logit_30d"
    assert manifest_payload["provenance"]["escalation"]["training"]["run_name"] == "train_country_week_logit_30d"
    assert manifest_payload["provenance"]["structural"]["training"]["run_name"] == "train_country_week_onset_structural_90d"
    assert forecast_snapshot_payload["primary_target"] == "onset"
    assert forecast_snapshot_payload["alert_type"] == "Onset Watch"
    assert forecast_snapshot_payload["no_clear_leader"] is False
    assert model_card_payload["threshold_policy"]["publish_threshold"] == 0.82
    assert model_card_payload["metrics"]["recall_at_10"] == 0.52
    assert model_card_payload["metrics"]["episode_recall"] == 0.44
    assert model_card_payload["provenance"]["structural"]["training"]["run_name"] == "train_country_week_onset_structural_90d"
    assert status_payload["primary_target"] == "onset"
    assert status_payload["alert_type"] == "Onset Watch"
    assert status_payload["no_clear_leader"] is False


def test_build_site_snapshot_publishes_no_clear_leader_when_latest_ranking_is_weak(tmp_path: Path) -> None:
    inputs = _write_publisher_inputs(tmp_path, preferred_exists=False)
    preferred_prediction_file = tmp_path / "artifacts" / "forecasting" / "predict" / "country_week_onset_logit" / "predictions.parquet"
    preferred_prediction_file.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(_tied_prediction_rows()).to_parquet(preferred_prediction_file, index=False)

    result = build_site_snapshot(
        run_name="site_snapshot",
        preferred_prediction_file=preferred_prediction_file,
        baseline_prediction_file=inputs["baseline_prediction_file"],
        training_manifest_file=inputs["training_manifest_file"],
        training_metrics_file=inputs["training_metrics_file"],
        calibration_metrics_file=inputs["calibration_metrics_file"],
        backtest_metrics_file=inputs["backtest_metrics_file"],
        baseline_training_manifest_file=inputs["baseline_training_manifest_file"],
        baseline_training_metrics_file=inputs["baseline_training_metrics_file"],
        baseline_calibration_metrics_file=inputs["baseline_calibration_metrics_file"],
        baseline_backtest_metrics_file=inputs["baseline_backtest_metrics_file"],
        report_inputs_file=inputs["report_inputs_file"],
        output_dir=tmp_path / "artifacts" / "website_publishing" / "site_snapshot" / "latest",
        published_at="2026-03-28T12:00:00Z",
        fresh_window_days=10,
        stale_window_days=21,
        publish_top_n=10,
        alert_threshold=0.7,
        warning_threshold=0.5,
        operating_threshold=0.6,
    )

    manifest_payload = json.loads(result.manifest_file.read_text(encoding="utf-8"))
    forecast_snapshot_payload = json.loads(result.forecast_snapshot_file.read_text(encoding="utf-8"))
    status_payload = json.loads(result.status_file.read_text(encoding="utf-8"))

    assert manifest_payload["alert_type"] == "No Clear Leader"
    assert manifest_payload["no_clear_leader"] is True
    assert forecast_snapshot_payload["alert_type"] == "No Clear Leader"
    assert forecast_snapshot_payload["no_clear_leader"] is True
    assert status_payload["alert_type"] == "No Clear Leader"
    assert status_payload["no_clear_leader"] is True


def test_run_publish_loads_yaml_config_and_writes_snapshot_bundle(tmp_path: Path) -> None:
    inputs = _write_publisher_inputs(tmp_path)
    config_path = _write_config(tmp_path, inputs)

    result = run_publish(config_path=config_path)

    assert result.output_dir.exists()
    assert result.manifest_file.exists()
    assert result.forecast_snapshot_file.exists()
