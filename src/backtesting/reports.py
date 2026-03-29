from __future__ import annotations

from pathlib import Path
from typing import Any


def write_backtest_report(
    path: Path,
    *,
    run_name: str,
    target_name: str,
    primary_model: str,
    baseline_model: str | None,
    model_metrics: dict[str, Any],
    comparison_summary: dict[str, Any],
    alert_metrics: dict[str, Any],
    calibration_method: str,
    plot_references: dict[str, str],
) -> Path:
    def _metric(name: str) -> Any:
        return alert_metrics.get(name, "n/a")

    baseline_label = baseline_model if baseline_model is not None else "unavailable"
    lines = [
        f"# Backtest Summary: {run_name}",
        "",
        f"- Target: `{target_name}`",
        f"- Primary model: `{primary_model}`",
        f"- Baseline model: `{baseline_label}`",
        f"- Primary model drives alerts, plots, and default replay: `{primary_model}`",
        "",
    ]
    top_model = comparison_summary.get("top_model")
    if top_model is not None:
        lines.extend(
            [
                "## Top-performing Model",
                "",
                f"- Top-performing model: `{top_model['model_name']}`",
                f"- PR AUC: `{top_model['pr_auc']}`",
                f"- ROC AUC: `{top_model['roc_auc']}`",
                f"- F1: `{top_model['f1']}`",
                f"- Brier score: `{top_model['brier_score']}`",
                "",
            ]
        )
    lines.extend(["## Model Metrics", ""])
    for model_name, payload in model_metrics.items():
        overall = payload["overall"]
        if overall is None:
            continue
        lines.extend(
            [
                f"### {model_name}",
                "",
                f"- Precision: `{overall['precision']}`",
                f"- Recall: `{overall['recall']}`",
                f"- F1: `{overall['f1']}`",
                f"- PR AUC: `{overall['pr_auc']}`",
                f"- ROC AUC: `{overall['roc_auc']}`",
                f"- Brier score: `{overall['brier_score']}`",
                "",
            ]
        )
    lines.extend(["## Baseline Comparison", ""])
    if comparison_summary["baseline_model"] is None or not comparison_summary["baseline_deltas"]:
        lines.extend(["- Baseline comparison unavailable for this run.", ""])
    else:
        for item in comparison_summary["baseline_deltas"]:
            lines.extend(
            [
                f"### {item['model_name']} vs {comparison_summary['baseline_model']}",
                "",
                f"- Delta PR AUC: `{item['delta_pr_auc']}`",
                f"- Delta ROC AUC: `{item['delta_roc_auc']}`",
                f"- Delta F1: `{item['delta_f1']}`",
                f"- Delta Brier score (candidate - baseline; lower is better): `{item['delta_brier_score']}` (negative is better)",
                "",
            ]
        )
    lines.extend(
        [
            "## Calibration",
            "",
            f"- Calibration method: `{calibration_method}`",
            "- Calibration note: per-fold calibrators are fit on each training slice before scoring the held-out fold.",
            "",
        ]
    )
    lines.extend(
        [
            "## Alert Metrics",
            "",
            f"- Publish threshold: `{_metric('publish_threshold')}`",
            f"- Alert threshold: `{_metric('alert_threshold')}`",
            f"- New alerts: `{_metric('new_alert_count')}`",
            f"- True alerts: `{_metric('true_alert_count')}`",
            f"- False alerts: `{_metric('false_alert_count')}`",
            f"- Label episodes: `{_metric('new_label_episode_count')}`",
            f"- Episode recall: `{_metric('episode_recall')}`",
            f"- False alerts per true alert: `{_metric('false_alerts_per_true_alert')}`",
            f"- Recall@5: `{_metric('recall_at_5')}`",
            f"- Recall@10: `{_metric('recall_at_10')}`",
            f"- No clear leader rate: `{_metric('no_clear_leader_rate')}`",
            f"- Mean lead days: `{_metric('first_alert_lead_days_mean')}`",
            f"- Median lead days: `{_metric('first_alert_lead_days_median')}`",
            f"- False alert burden: `{_metric('false_alert_burden')}`",
            "",
            "## Plots",
            "",
            f"- Probability distribution: `{plot_references['probability_distribution']}`",
            f"- Precision-recall curve: `{plot_references['precision_recall']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_replay_report(
    path: Path,
    *,
    entity_id: str,
    model_name: str,
    comparison_top_model: str | None = None,
    replay_rows: list[dict[str, object]],
) -> Path:
    lines = [f"# Replay: {entity_id}", "", f"- Model: `{model_name}`"]
    if comparison_top_model is not None and comparison_top_model != model_name:
        lines.append(f"- Top-performing backtest model: `{comparison_top_model}`")
    lines.append("")
    for row in replay_rows:
        lines.extend(
            [
                f"## {row['forecast_date']}",
                "",
                f"- Probability: `{row['calibrated_probability']}`",
                f"- Label: `{row['label']}`",
                f"- Alert: `{row['is_alert']}`",
                f"- Outcome: `{row['alert_outcome']}`",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
