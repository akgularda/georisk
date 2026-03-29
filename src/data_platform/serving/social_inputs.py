from __future__ import annotations

import json

import pandas as pd

from src.data_platform.serving.report_inputs import (
    _country_week_with_scores,
    _event_phrase,
    _latest_country_week_rows,
    latest_label_targets_are_known,
    predicted_conflict_from_row,
    risk_level_from_score,
    source_snapshot_hash_from_row,
    top_driver_strings_from_row,
)


SOCIAL_INPUT_COLUMNS = [
    "post_id",
    "platform_name",
    "country_iso3",
    "country_name",
    "publish_date",
    "as_of_date",
    "forecast_target",
    "forecast_horizon_days",
    "forecast_probability",
    "score_delta",
    "summary_line",
    "top_drivers",
    "report_slug",
    "headline",
    "body",
    "call_to_action",
    "destination_url",
    "source_snapshot_hash",
    "snapshot_ts_utc",
]


def _empty_social_inputs() -> pd.DataFrame:
    return pd.DataFrame(columns=SOCIAL_INPUT_COLUMNS)


def build_gold_social_inputs(country_week_features: pd.DataFrame) -> pd.DataFrame:
    if country_week_features.empty:
        return _empty_social_inputs()

    weekly = _country_week_with_scores(country_week_features)
    latest_rows = _latest_country_week_rows(weekly)
    social_rows: list[dict[str, object]] = []

    for _, row in latest_rows.iterrows():
        country_history = weekly.loc[weekly["country_iso3"] == row["country_iso3"]].sort_values("week_start_date").reset_index(drop=True)
        current_score = None if pd.isna(row["risk_score"]) else float(row["risk_score"])
        previous_score = None
        if len(country_history) > 1 and not pd.isna(country_history.iloc[-2]["risk_score"]):
            previous_score = float(country_history.iloc[-2]["risk_score"])
        if current_score is not None and previous_score is not None:
            score_delta = round(current_score - previous_score, 1)
        elif current_score is not None and len(country_history) == 1:
            score_delta = 0.0
        else:
            score_delta = pd.NA
        risk_level = risk_level_from_score(current_score) if current_score is not None else pd.NA
        previous_risk_level = risk_level_from_score(previous_score) if previous_score is not None else None
        slug = f"{str(row['country_iso3']).lower()}-latest"
        publish_date = (pd.Timestamp(row["week_start_date"]) + pd.Timedelta(days=6)).date()
        top_driver_values = top_driver_strings_from_row(row)
        top_drivers = json.dumps(top_driver_values)
        predicted_conflict_label, _, _ = predicted_conflict_from_row(row)
        acled_phrase = _event_phrase(int(top_driver_values[0].split(": ", 1)[1]), "ACLED event")
        gdelt_phrase = _event_phrase(int(top_driver_values[1].split(": ", 1)[1]), "GDELT event")
        if current_score is None or not latest_label_targets_are_known(row):
            summary_line = (
                f"{row['country_name']} remains on the current monitoring board. Latest signals show "
                f"{acled_phrase} over 28 days and {gdelt_phrase} over 7 days."
            )
            headline = f"{row['country_name']} monitoring update: signal watch"
        elif previous_risk_level is None:
            summary_line = (
                f"{row['country_name']} enters the {risk_level} monitoring band after "
                f"{acled_phrase} over 28 days and {gdelt_phrase} over 7 days."
            )
            headline = f"{row['country_name']} monitoring update: {risk_level}"
        elif previous_risk_level == risk_level:
            summary_line = (
                f"{row['country_name']} remains in the {risk_level} monitoring band after "
                f"{acled_phrase} over 28 days and {gdelt_phrase} over 7 days."
            )
            headline = f"{row['country_name']} monitoring update: {risk_level}"
        else:
            summary_line = (
                f"{row['country_name']} moved into the {risk_level} monitoring band after "
                f"{acled_phrase} over 28 days and {gdelt_phrase} over 7 days."
            )
            headline = f"{row['country_name']} monitoring update: {risk_level}"
        body = f"{summary_line} Drivers: {', '.join(json.loads(top_drivers))}."
        social_rows.append(
            {
                "post_id": f"post-{slug}",
                "platform_name": "generic",
                "country_iso3": row["country_iso3"],
                "country_name": row["country_name"],
                "publish_date": publish_date,
                "as_of_date": publish_date,
                "forecast_target": "label_escalation_30d",
                "forecast_horizon_days": 30,
                "forecast_probability": current_score,
                "score_delta": score_delta,
                "summary_line": summary_line,
                "top_drivers": top_drivers,
                "report_slug": slug,
                "headline": headline,
                "body": body,
                "call_to_action": "Review the latest country monitoring brief.",
                "destination_url": f"/countries/{slug}",
                "source_snapshot_hash": source_snapshot_hash_from_row(row),
                "snapshot_ts_utc": row["snapshot_ts_utc"],
            }
        )

    social_inputs = pd.DataFrame.from_records(social_rows).sort_values("country_iso3").reset_index(drop=True)
    return social_inputs[SOCIAL_INPUT_COLUMNS]
