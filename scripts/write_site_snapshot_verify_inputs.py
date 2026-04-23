from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "website_publishing" / "site_snapshot.yaml"


def _resolve_path(value: object) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_absolute() else REPO_ROOT / path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prediction_rows(
    *,
    model_name: str,
    model_version: str,
    target_name: str,
    calibration_run_name: str,
    calibration_training_run_name: str,
) -> list[dict[str, object]]:
    base_rows = [
        {
            "country_iso3": "LBN",
            "country_name": "Lebanon",
            "region_name": "Middle East",
            "forecast_date": "2026-03-23",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
            "calibrated_probability": 0.84,
            "training_window_id": "2015-01-05_2026-02-23",
            "feature_snapshot_hash": "verify-hash-lbn-1",
            "top_positive_drivers": [
                {"feature": "acled_event_count_28d", "contribution": 1.2},
                {"feature": "gdelt_event_count_7d", "contribution": 0.6},
            ],
        },
        {
            "country_iso3": "LBN",
            "country_name": "Lebanon",
            "region_name": "Middle East",
            "forecast_date": "2026-03-16",
            "snapshot_ts_utc": "2026-03-21T06:00:00Z",
            "calibrated_probability": 0.78,
            "training_window_id": "2015-01-05_2026-02-16",
            "feature_snapshot_hash": "verify-hash-lbn-0",
            "top_positive_drivers": [
                {"feature": "acled_event_count_28d", "contribution": 1.1},
                {"feature": "market_oil_price_usd_per_barrel", "contribution": 0.3},
            ],
        },
        {
            "country_iso3": "ISR",
            "country_name": "Israel",
            "region_name": "Middle East",
            "forecast_date": "2026-03-23",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
            "calibrated_probability": 0.79,
            "training_window_id": "2015-01-05_2026-02-23",
            "feature_snapshot_hash": "verify-hash-isr-1",
            "top_positive_drivers": [
                {"feature": "gdelt_num_mentions_7d", "contribution": 0.8},
                {"feature": "security_military_expenditure_pct_gdp", "contribution": 0.5},
            ],
        },
        {
            "country_iso3": "ISR",
            "country_name": "Israel",
            "region_name": "Middle East",
            "forecast_date": "2026-03-16",
            "snapshot_ts_utc": "2026-03-21T06:00:00Z",
            "calibrated_probability": 0.74,
            "training_window_id": "2015-01-05_2026-02-16",
            "feature_snapshot_hash": "verify-hash-isr-0",
            "top_positive_drivers": [
                {"feature": "gdelt_num_mentions_7d", "contribution": 0.6},
                {"feature": "shipping_lsci_index", "contribution": 0.4},
            ],
        },
    ]
    rows = []
    for row in base_rows:
        rows.append(
            {
                **row,
                "model_name": model_name,
                "model_version": model_version,
                "target_name": target_name,
                "horizon_days": 30,
                "calibration_run_name": calibration_run_name,
                "calibration_model_name": model_name,
                "calibration_training_run_name": calibration_training_run_name,
                "top_positive_drivers": json.dumps(row["top_positive_drivers"]),
            }
        )
    return rows


def _report_input_rows() -> list[dict[str, object]]:
    conflict_countries = json.dumps(
        [
            {"iso3": "LBN", "country_name": "Lebanon"},
            {"iso3": "ISR", "country_name": "Israel"},
        ]
    )
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
            "predicted_conflict_countries": conflict_countries,
            "reason_source": "report_inputs",
            "chronology": json.dumps(
                [
                    "Week of 2026-03-23: cross-border pressure remained elevated.",
                    "Trailing 28-day ACLED events: 12.",
                ]
            ),
            "top_drivers": json.dumps(["ACLED events (28d): 12", "GDELT events (7d): 9"]),
            "top_drivers_json": json.dumps(["ACLED events (28d): 12", "GDELT events (7d): 9"]),
            "source_snapshot_hash": "verify-report-lbn-hash",
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
            "predicted_conflict_countries": conflict_countries,
            "reason_source": "report_inputs",
            "chronology": json.dumps(
                [
                    "Week of 2026-03-23: deterrence language hardened.",
                    "Trailing 28-day ACLED events: 7.",
                ]
            ),
            "top_drivers": json.dumps(["GDELT mentions (7d): 16", "Shipping LSCI: 92"]),
            "top_drivers_json": json.dumps(["GDELT mentions (7d): 16", "Shipping LSCI: 92"]),
            "source_snapshot_hash": "verify-report-isr-hash",
            "snapshot_ts_utc": "2026-03-28T06:00:00Z",
        },
    ]


def _training_manifest(
    *,
    run_name: str,
    primary_model: str,
    target_name: str,
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


def _training_metrics(model_name: str) -> dict[str, object]:
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
            },
        },
    }


def _calibration_metrics(*, model_name: str, run_name: str, training_run_name: str) -> dict[str, object]:
    return {
        "run_name": run_name,
        "method": "isotonic",
        "model_name": model_name,
        "training_run_name": training_run_name,
        "training_window_id": "2015-01-05_2026-02-23",
        "metrics": {
            "roc_auc": 0.81,
            "brier_score": 0.14,
        },
    }


def _backtest_metrics(model_name: str, *, top_model_name: str | None = None) -> dict[str, object]:
    return {
        "primary_model": model_name,
        "baseline_model": "prior_rate",
        "comparison": {
            "top_model": {"model_name": top_model_name or model_name},
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


def _write_prediction_file(path: Path | None, rows: list[dict[str, object]]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)


def _write_report_inputs(path: Path | None) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(_report_input_rows()).to_parquet(path, index=False)


def write_inputs(config_path: Path = DEFAULT_CONFIG_PATH) -> None:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    _write_prediction_file(
        _resolve_path(config.get("preferred_prediction_file")),
        _prediction_rows(
            model_name="logit",
            model_version="country_week_onset_logit_30d",
            target_name="country_week_onset_30d",
            calibration_run_name="country_week_onset_logit",
            calibration_training_run_name="train_country_week_onset_logit_30d",
        ),
    )
    _write_prediction_file(
        _resolve_path(config.get("secondary_prediction_file")),
        _prediction_rows(
            model_name="logit",
            model_version="country_week_logit_30d",
            target_name="country_week_escalation_30d",
            calibration_run_name="country_week_logit",
            calibration_training_run_name="train_country_week_logit_30d",
        ),
    )
    _write_prediction_file(
        _resolve_path(config.get("baseline_prediction_file")),
        _prediction_rows(
            model_name="prior_rate",
            model_version="country_week_default_30d",
            target_name="country_week_escalation_30d",
            calibration_run_name="country_week_default",
            calibration_training_run_name="train_country_week_30d",
        ),
    )
    _write_report_inputs(_resolve_path(config.get("report_inputs_file")))

    metadata_specs = {
        "training": {
            "manifest_key": "training_manifest_file",
            "metrics_key": "training_metrics_file",
            "calibration_key": "calibration_metrics_file",
            "backtest_key": "backtest_metrics_file",
            "run_name": "train_country_week_onset_logit_30d",
            "model_name": "logit",
            "target_name": "country_week_onset_30d",
            "calibration_run_name": "country_week_onset_logit",
            "calibration_training_run_name": "train_country_week_onset_logit_30d",
            "horizon_days": 30,
        },
        "secondary": {
            "manifest_key": "secondary_training_manifest_file",
            "metrics_key": "secondary_training_metrics_file",
            "calibration_key": "secondary_calibration_metrics_file",
            "backtest_key": "secondary_backtest_metrics_file",
            "run_name": "train_country_week_logit_30d",
            "model_name": "logit",
            "target_name": "country_week_escalation_30d",
            "calibration_run_name": "country_week_logit",
            "calibration_training_run_name": "train_country_week_logit_30d",
            "horizon_days": 30,
        },
        "structural": {
            "manifest_key": "structural_training_manifest_file",
            "metrics_key": None,
            "calibration_key": "structural_calibration_metrics_file",
            "backtest_key": "structural_backtest_metrics_file",
            "run_name": "train_country_week_onset_structural_90d",
            "model_name": "logit",
            "target_name": "country_week_onset_90d",
            "calibration_run_name": "country_week_onset_structural_90d",
            "calibration_training_run_name": "train_country_week_onset_structural_90d",
            "horizon_days": 90,
        },
        "baseline": {
            "manifest_key": "baseline_training_manifest_file",
            "metrics_key": "baseline_training_metrics_file",
            "calibration_key": "baseline_calibration_metrics_file",
            "backtest_key": "baseline_backtest_metrics_file",
            "run_name": "train_country_week_30d",
            "model_name": "prior_rate",
            "target_name": "country_week_escalation_30d",
            "calibration_run_name": "country_week_default",
            "calibration_training_run_name": "train_country_week_30d",
            "horizon_days": 30,
        },
    }

    for spec in metadata_specs.values():
        manifest_path = _resolve_path(config.get(spec["manifest_key"]))
        if manifest_path is not None:
            _write_json(
                manifest_path,
                _training_manifest(
                    run_name=str(spec["run_name"]),
                    primary_model=str(spec["model_name"]),
                    target_name=str(spec["target_name"]),
                    horizon_days=int(spec["horizon_days"]),
                ),
            )

        metrics_key = spec["metrics_key"]
        metrics_path = _resolve_path(config.get(metrics_key)) if metrics_key is not None else None
        if metrics_path is not None:
            _write_json(metrics_path, _training_metrics(str(spec["model_name"])))

        calibration_path = _resolve_path(config.get(spec["calibration_key"]))
        if calibration_path is not None:
            _write_json(
                calibration_path,
                _calibration_metrics(
                    model_name=str(spec["model_name"]),
                    run_name=str(spec["calibration_run_name"]),
                    training_run_name=str(spec["calibration_training_run_name"]),
                ),
            )

        backtest_path = _resolve_path(config.get(spec["backtest_key"]))
        if backtest_path is not None:
            _write_json(backtest_path, _backtest_metrics(str(spec["model_name"])))


def main() -> None:
    parser = argparse.ArgumentParser(description="Write deterministic site snapshot verify inputs.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    write_inputs(args.config)


if __name__ == "__main__":
    main()
