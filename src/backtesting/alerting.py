from __future__ import annotations

import pandas as pd


def build_alert_table(predictions: pd.DataFrame, *, threshold: float, gap_days: int) -> pd.DataFrame:
    working = predictions.copy()
    working["forecast_date"] = pd.to_datetime(working["forecast_date"]).dt.normalize()
    working = working.sort_values(by=["entity_id", "forecast_date"], kind="mergesort").reset_index(drop=True)
    working["is_alert"] = working["calibrated_probability"].astype(float) >= threshold
    working["label"] = working["label"].astype(int)

    alert_episode_ids: list[str | None] = []
    label_episode_ids: list[str | None] = []
    is_new_alert_flags: list[int] = []
    is_new_label_flags: list[int] = []

    for _, group in working.groupby("entity_id", sort=False):
        last_alert_date = None
        last_label_date = None
        alert_index = 0
        label_index = 0
        for row in group.itertuples():
            current_date = pd.Timestamp(row.forecast_date)
            if bool(row.is_alert):
                is_new_alert = int(last_alert_date is None or (current_date - last_alert_date).days > gap_days)
                if is_new_alert:
                    alert_index += 1
                alert_episode_id = f"{row.entity_id}-alert-{alert_index:03d}"
                last_alert_date = current_date
            else:
                is_new_alert = 0
                alert_episode_id = None

            if int(row.label) == 1:
                is_new_label = int(last_label_date is None or (current_date - last_label_date).days > gap_days)
                if is_new_label:
                    label_index += 1
                label_episode_id = f"{row.entity_id}-label-{label_index:03d}"
                last_label_date = current_date
            else:
                is_new_label = 0
                label_episode_id = None

            alert_episode_ids.append(alert_episode_id)
            label_episode_ids.append(label_episode_id)
            is_new_alert_flags.append(is_new_alert)
            is_new_label_flags.append(is_new_label)

    working["alert_episode_id"] = alert_episode_ids
    working["label_episode_id"] = label_episode_ids
    working["is_new_alert"] = is_new_alert_flags
    working["is_new_label_episode"] = is_new_label_flags

    outcomes: list[str | None] = []
    lead_days: list[int | None] = []
    for _, group in working.groupby("entity_id", sort=False):
        positive_dates = group.loc[group["label"] == 1, "forecast_date"]
        for row in group.itertuples():
            if not row.is_alert or row.alert_episode_id is None:
                outcomes.append(None)
                lead_days.append(None)
                continue
            future_positive_dates = positive_dates.loc[positive_dates >= row.forecast_date]
            if future_positive_dates.empty:
                outcomes.append("false_alert")
                lead_days.append(None)
                continue
            first_positive_date = future_positive_dates.iloc[0]
            lead_day = int((first_positive_date - row.forecast_date).days)
            outcomes.append("true_alert")
            lead_days.append(lead_day)

    working["alert_outcome"] = outcomes
    working["lead_days_to_positive_label"] = lead_days
    return working

