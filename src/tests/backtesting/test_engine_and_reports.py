from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.backtesting.engine import _resolve_requested_models
from src.backtesting.evaluators import select_operating_threshold, summarize_model_comparison, summarize_ranking_metrics
from src.backtesting.reports import write_backtest_report, write_replay_report

def test_resolve_requested_models_requires_configured_models() -> None:
    with pytest.raises(ValueError, match="Configured primary model `logit` was not produced"):
        _resolve_requested_models(primary_model="logit", baseline_model=None, available_models=["prior_rate"])

    with pytest.raises(ValueError, match="Configured baseline model `prior_rate` was not produced"):
        _resolve_requested_models(primary_model="logit", baseline_model="prior_rate", available_models=["logit"])

    primary_model, baseline_model = _resolve_requested_models(
        primary_model="logit",
        baseline_model=None,
        available_models=["prior_rate", "logit"],
    )
    assert primary_model == "logit"
    assert baseline_model == "prior_rate"

    primary_model, baseline_model = _resolve_requested_models(
        primary_model="logit",
        baseline_model=None,
        available_models=["logit"],
    )
    assert primary_model == "logit"
    assert baseline_model is None


def test_model_comparison_deltas_use_consistent_candidate_minus_baseline_sign() -> None:
    summary = summarize_model_comparison(
        {
            "prior_rate": {
                "overall": {
                    "precision": 0.1,
                    "recall": 0.2,
                    "f1": 0.3,
                    "pr_auc": 0.4,
                    "roc_auc": 0.5,
                    "brier_score": 0.2,
                }
            },
            "logit": {
                "overall": {
                    "precision": 0.2,
                    "recall": 0.3,
                    "f1": 0.4,
                    "pr_auc": 0.6,
                    "roc_auc": 0.7,
                    "brier_score": 0.1,
                }
            },
        },
        baseline_model="prior_rate",
    )

    assert summary["baseline_deltas"] == [
        {
            "model_name": "logit",
            "delta_pr_auc": pytest.approx(0.2),
            "delta_roc_auc": pytest.approx(0.2),
            "delta_f1": pytest.approx(0.1),
            "delta_brier_score": pytest.approx(-0.1),
        }
    ]


def test_operating_threshold_prefers_episode_recall_without_extra_false_alerts() -> None:
    predictions = pd.DataFrame(
        {
            "entity_id": ["A", "A", "B", "B"],
            "forecast_date": pd.to_datetime(["2025-01-01", "2025-01-08", "2025-01-01", "2025-01-08"]),
            "calibrated_probability": [0.9, 0.8, 0.7, 0.6],
            "label": [0, 1, 0, 0],
        }
    )

    threshold_summary = select_operating_threshold(predictions, gap_days=30)
    ranking_metrics = summarize_ranking_metrics(predictions, publish_threshold=threshold_summary["publish_threshold"])

    assert threshold_summary["publish_threshold"] == pytest.approx(0.9)
    assert threshold_summary["episode_recall"] == pytest.approx(1.0)
    assert threshold_summary["false_alert_count"] == 0
    assert ranking_metrics["recall_at_5"] == pytest.approx(1.0)
    assert ranking_metrics["recall_at_10"] == pytest.approx(1.0)
    assert ranking_metrics["no_clear_leader_rate"] == pytest.approx(0.5)


def test_reports_make_primary_and_replay_model_explicit(tmp_path: Path) -> None:
    report_path = write_backtest_report(
        tmp_path / "summary.md",
        run_name="country_week_logit",
        target_name="country_week_escalation_30d",
        primary_model="logit",
        baseline_model="prior_rate",
        model_metrics={
            "prior_rate": {
                "overall": {
                    "precision": 0.1,
                    "recall": 0.2,
                    "f1": 0.3,
                    "pr_auc": 0.4,
                    "roc_auc": 0.5,
                    "brier_score": 0.2,
                }
            },
            "logit": {
                "overall": {
                    "precision": 0.2,
                    "recall": 0.3,
                    "f1": 0.4,
                    "pr_auc": 0.6,
                    "roc_auc": 0.7,
                    "brier_score": 0.1,
                }
            },
        },
        comparison_summary={
            "baseline_model": "prior_rate",
            "top_model": {
                "model_name": "prior_rate",
                "pr_auc": 0.7,
                "roc_auc": 0.8,
                "f1": 0.5,
                "brier_score": 0.2,
            },
            "model_summaries": [],
            "baseline_deltas": [
                {
                    "model_name": "logit",
                    "delta_pr_auc": 0.2,
                    "delta_roc_auc": 0.2,
                    "delta_f1": 0.1,
                    "delta_brier_score": -0.1,
                }
            ],
        },
        alert_metrics={
            "publish_threshold": 0.9,
            "alert_threshold": 0.9,
            "new_alert_count": 1,
            "true_alert_count": 1,
            "false_alert_count": 0,
            "new_label_episode_count": 1,
            "episode_recall": 1.0,
            "false_alerts_per_true_alert": 0.0,
            "recall_at_5": 1.0,
            "recall_at_10": 1.0,
            "no_clear_leader_rate": 0.5,
            "first_alert_lead_days_mean": 5.0,
            "first_alert_lead_days_median": 5.0,
            "false_alert_burden": 0,
        },
        calibration_method="isotonic",
        plot_references={
            "probability_distribution": "probability_distribution.svg",
            "precision_recall": "precision_recall.svg",
        },
    )
    replay_path = write_replay_report(
        tmp_path / "replay.md",
        entity_id="IRN",
        model_name="logit",
        replay_rows=[
            {
                "forecast_date": "2025-01-01",
                "calibrated_probability": 0.75,
                "label": 1,
                "is_alert": 1,
                "alert_outcome": "true_alert",
            }
        ],
    )

    report_text = report_path.read_text(encoding="utf-8")
    replay_text = replay_path.read_text(encoding="utf-8")

    assert "Primary model drives alerts, plots, and default replay: `logit`" in report_text
    assert "Delta Brier score (candidate - baseline; lower is better): `-0.1`" in report_text
    assert "training slice" in report_text
    assert "Publish threshold: `0.9`" in report_text
    assert "Recall@5: `1.0`" in report_text
    assert "Recall@10: `1.0`" in report_text
    assert "Episode recall: `1.0`" in report_text
    assert "No clear leader rate: `0.5`" in report_text
    assert "- Model: `logit`" in replay_text
