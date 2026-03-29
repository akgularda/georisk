from __future__ import annotations

import math
from typing import Any

import pandas as pd

from src.backtesting.alerting import build_alert_table
from src.forecasting.metrics import compute_classification_metrics, compute_grouped_metrics


def evaluate_prediction_frame(
    frame: pd.DataFrame,
    *,
    probability_column: str,
    threshold: float,
    group_columns: list[str],
) -> dict[str, Any]:
    return {
        "overall": compute_classification_metrics(
            frame,
            probability_column=probability_column,
            threshold=threshold,
        ),
        "by_group": compute_grouped_metrics(
            frame,
            probability_column=probability_column,
            group_columns=group_columns,
            threshold=threshold,
        ),
    }


def summarize_alert_metrics(alert_table: pd.DataFrame) -> dict[str, Any]:
    new_alerts = alert_table.loc[alert_table["is_new_alert"] == 1].copy()
    new_label_episodes = int(alert_table["is_new_label_episode"].sum())
    true_alerts = new_alerts.loc[new_alerts["alert_outcome"] == "true_alert"]
    false_alerts = new_alerts.loc[new_alerts["alert_outcome"] == "false_alert"]
    recalled_episodes = 0
    if new_label_episodes > 0:
        label_episode_rows = alert_table.loc[
            (alert_table["is_new_label_episode"] == 1) & alert_table["label_episode_id"].notna(),
            ["entity_id", "label_episode_id", "forecast_date"],
        ].copy()
        label_episode_rows["forecast_date"] = pd.to_datetime(label_episode_rows["forecast_date"]).dt.normalize()
        normalized_alert_table = alert_table.copy()
        normalized_alert_table["forecast_date"] = pd.to_datetime(normalized_alert_table["forecast_date"]).dt.normalize()
        for row in label_episode_rows.itertuples():
            prior_true_alerts = normalized_alert_table.loc[
                (normalized_alert_table["entity_id"] == row.entity_id)
                & (normalized_alert_table["forecast_date"] <= row.forecast_date)
                & (normalized_alert_table["is_alert"] == 1)
                & (normalized_alert_table["alert_outcome"] == "true_alert")
            ]
            if not prior_true_alerts.empty:
                recalled_episodes += 1

    return {
        "new_alert_count": int(len(new_alerts)),
        "new_label_episode_count": new_label_episodes,
        "true_alert_count": int(len(true_alerts)),
        "false_alert_count": int(len(false_alerts)),
        "episode_recall": None if new_label_episodes == 0 else float(recalled_episodes / new_label_episodes),
        "first_alert_lead_days_mean": None if true_alerts.empty else float(true_alerts["lead_days_to_positive_label"].mean()),
        "first_alert_lead_days_median": None if true_alerts.empty else float(true_alerts["lead_days_to_positive_label"].median()),
        "false_alert_burden": int(len(false_alerts)),
        "false_alerts_per_true_alert": None if true_alerts.empty else float(len(false_alerts) / len(true_alerts)),
    }


def summarize_ranking_metrics(
    frame: pd.DataFrame,
    *,
    probability_column: str = "calibrated_probability",
    label_column: str = "label",
    date_column: str = "forecast_date",
    publish_threshold: float,
    top_k_values: tuple[int, ...] = (5, 10),
    no_clear_leader_margin: float = 0.02,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "no_clear_leader_rate": None,
            **{f"recall_at_{k_value}": None for k_value in top_k_values},
        }

    working = frame.copy()
    working[date_column] = pd.to_datetime(working[date_column]).dt.normalize()
    working[probability_column] = working[probability_column].astype(float)
    working[label_column] = working[label_column].astype(int)
    positive_count = int(working[label_column].sum())

    ranking_metrics: dict[str, Any] = {}
    for k_value in top_k_values:
        captured_positives = 0
        for _, group in working.groupby(date_column, sort=False):
            ranked = group.sort_values(by=probability_column, ascending=False, kind="mergesort").head(k_value)
            captured_positives += int(ranked[label_column].sum())
        ranking_metrics[f"recall_at_{k_value}"] = None if positive_count == 0 else float(captured_positives / positive_count)

    no_clear_leader_count = 0
    total_dates = 0
    for _, group in working.groupby(date_column, sort=False):
        ranked = group.sort_values(by=probability_column, ascending=False, kind="mergesort")
        if ranked.empty:
            continue
        total_dates += 1
        top_probability = float(ranked.iloc[0][probability_column])
        second_probability = float(ranked.iloc[1][probability_column]) if len(ranked) > 1 else None
        no_clear_leader = top_probability < publish_threshold
        if second_probability is not None and (top_probability - second_probability) < no_clear_leader_margin:
            no_clear_leader = True
        no_clear_leader_count += int(no_clear_leader)

    ranking_metrics["no_clear_leader_rate"] = None if total_dates == 0 else float(no_clear_leader_count / total_dates)
    return ranking_metrics


def select_operating_threshold(
    predictions: pd.DataFrame,
    *,
    gap_days: int,
    probability_column: str = "calibrated_probability",
) -> dict[str, Any]:
    if predictions.empty:
        return {
            "publish_threshold": 0.5,
            "alert_threshold": 0.5,
            "episode_recall": None,
            "true_alert_count": 0,
            "false_alert_count": 0,
        }

    candidate_thresholds = sorted({float(value) for value in predictions[probability_column].astype(float).tolist()}, reverse=True)
    if not candidate_thresholds:
        candidate_thresholds = [0.5]

    best_summary: dict[str, Any] | None = None
    best_score: tuple[float, float, float, float] | None = None
    for threshold in candidate_thresholds:
        alerts = build_alert_table(predictions, threshold=threshold, gap_days=gap_days)
        summary = summarize_alert_metrics(alerts)
        summary["publish_threshold"] = float(threshold)
        summary["alert_threshold"] = float(threshold)
        score = (
            -1.0 if summary["episode_recall"] is None else float(summary["episode_recall"]),
            float(summary["true_alert_count"]),
            -float(summary["false_alert_count"]),
            float(threshold),
        )
        if best_score is None or score > best_score:
            best_summary = summary
            best_score = score

    assert best_summary is not None
    return best_summary


def summarize_model_comparison(
    model_metrics: dict[str, dict[str, Any]],
    *,
    baseline_model: str | None,
) -> dict[str, Any]:
    model_summaries: list[dict[str, Any]] = []
    for model_name, payload in model_metrics.items():
        overall = payload.get("overall")
        if overall is None:
            continue
        model_summaries.append(
            {
                "model_name": model_name,
                "precision": overall.get("precision"),
                "recall": overall.get("recall"),
                "f1": overall.get("f1"),
                "pr_auc": overall.get("pr_auc"),
                "roc_auc": overall.get("roc_auc"),
                "brier_score": overall.get("brier_score"),
            }
        )

    baseline_summary = next((item for item in model_summaries if item["model_name"] == baseline_model), None)

    def _sort_key(summary: dict[str, Any]) -> tuple[float, float, float, float]:
        pr_auc = -math.inf if summary["pr_auc"] is None else float(summary["pr_auc"])
        roc_auc = -math.inf if summary["roc_auc"] is None else float(summary["roc_auc"])
        f1 = -math.inf if summary["f1"] is None else float(summary["f1"])
        brier = math.inf if summary["brier_score"] is None else float(summary["brier_score"])
        return (pr_auc, roc_auc, f1, -brier)

    top_model = max(model_summaries, key=_sort_key) if model_summaries else None

    def _delta(candidate: float | None, baseline: float | None) -> float | None:
        if candidate is None or baseline is None:
            return None
        return float(candidate - baseline)

    baseline_deltas: list[dict[str, Any]] = []
    if baseline_summary is not None:
        for summary in model_summaries:
            if summary["model_name"] == baseline_summary["model_name"]:
                continue
            baseline_deltas.append(
                {
                    "model_name": summary["model_name"],
                    "delta_pr_auc": _delta(summary["pr_auc"], baseline_summary["pr_auc"]),
                    "delta_roc_auc": _delta(summary["roc_auc"], baseline_summary["roc_auc"]),
                    "delta_f1": _delta(summary["f1"], baseline_summary["f1"]),
                    "delta_brier_score": _delta(summary["brier_score"], baseline_summary["brier_score"]),
                }
            )

    return {
        "baseline_model": baseline_summary["model_name"] if baseline_summary is not None else None,
        "top_model": top_model,
        "model_summaries": model_summaries,
        "baseline_deltas": baseline_deltas,
    }
