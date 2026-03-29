from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score


def _safe_metric(metric_fn, y_true: np.ndarray, y_score: np.ndarray) -> float | None:
    try:
        return float(metric_fn(y_true, y_score))
    except ValueError:
        return None


def compute_classification_metrics(
    frame: pd.DataFrame,
    *,
    probability_column: str,
    label_column: str = "label",
    threshold: float = 0.5,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "pr_auc": None,
            "roc_auc": None,
            "brier_score": None,
            "calibration_curve": [],
            "false_positives_per_true_positive": None,
            "top_k_risk_hit_rate": None,
        }

    y_true = frame[label_column].astype(int).to_numpy()
    y_prob = frame[probability_column].astype(float).clip(0.0, 1.0).to_numpy()
    y_pred = (y_prob >= threshold).astype(int)
    unique_labels = np.unique(y_true)

    if len(unique_labels) >= 2:
        calibration_x, calibration_y = calibration_curve(y_true, y_prob, n_bins=5, strategy="quantile")
    else:
        calibration_x = np.asarray([float(y_prob.mean())], dtype=float)
        calibration_y = np.asarray([float(y_true.mean())], dtype=float)
    positives = max(int(y_true.sum()), 1)
    top_k_indices = np.argsort(y_prob)[::-1][:positives]
    top_k_hit_rate = float(y_true[top_k_indices].sum() / len(top_k_indices)) if len(top_k_indices) > 0 else None

    true_positives = int(((y_pred == 1) & (y_true == 1)).sum())
    false_positives = int(((y_pred == 1) & (y_true == 0)).sum())
    false_positive_ratio = None if true_positives == 0 else float(false_positives / true_positives)

    metrics: dict[str, Any] = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "pr_auc": None if int(y_true.sum()) == 0 else _safe_metric(average_precision_score, y_true, y_prob),
        "roc_auc": None if len(unique_labels) < 2 else _safe_metric(roc_auc_score, y_true, y_prob),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "calibration_curve": [
            {"predicted_bin_probability": float(x_value), "observed_rate": float(y_value)}
            for x_value, y_value in zip(calibration_x, calibration_y, strict=False)
        ],
        "false_positives_per_true_positive": false_positive_ratio,
        "top_k_risk_hit_rate": top_k_hit_rate,
    }

    if "next_event_date" in frame.columns and "as_of_date" in frame.columns:
        alerted_positives = frame.loc[(y_pred == 1) & frame["next_event_date"].notna()].copy()
        if not alerted_positives.empty:
            lead_days = (
                pd.to_datetime(alerted_positives["next_event_date"]) - pd.to_datetime(alerted_positives["as_of_date"])
            ).dt.days
            metrics["lead_time_metrics"] = {
                "mean_lead_days": float(lead_days.mean()),
                "median_lead_days": float(lead_days.median()),
            }
        else:
            metrics["lead_time_metrics"] = {
                "mean_lead_days": None,
                "median_lead_days": None,
            }
    return metrics


def compute_grouped_metrics(
    frame: pd.DataFrame,
    *,
    probability_column: str,
    group_columns: list[str],
    label_column: str = "label",
    threshold: float = 0.5,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(dict)
    for column in group_columns:
        if column not in frame.columns:
            continue
        for group_value, group_frame in frame.groupby(column):
            grouped[column][str(group_value)] = compute_classification_metrics(
                group_frame,
                probability_column=probability_column,
                label_column=label_column,
                threshold=threshold,
            )
    return dict(grouped)
