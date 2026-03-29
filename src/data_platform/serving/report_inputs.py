from __future__ import annotations

import hashlib
import json
from datetime import date

import pandas as pd

from src.ai.openrouter import maybe_generate_country_narrative

REPORT_INPUT_COLUMNS = [
    "report_id",
    "report_slug",
    "report_title",
    "country_iso3",
    "country_name",
    "region_name",
    "report_date",
    "as_of_date",
    "forecast_horizon_days",
    "forecast_target",
    "forecast_probability",
    "risk_level",
    "freshness_days",
    "summary",
    "predicted_conflict_label",
    "predicted_conflict_countries",
    "reason_source",
    "chronology",
    "top_drivers",
    "top_drivers_json",
    "source_snapshot_hash",
    "snapshot_ts_utc",
]

CURATED_CONFLICTS_BY_ISO3: dict[str, list[dict[str, str]]] = {
    "CHN": [
        {"iso3": "TWN", "country_name": "Taiwan"},
        {"iso3": "CHN", "country_name": "China"},
    ],
    "IRN": [
        {"iso3": "IRN", "country_name": "Iran"},
        {"iso3": "ISR", "country_name": "Israel"},
    ],
    "ISR": [
        {"iso3": "IRN", "country_name": "Iran"},
        {"iso3": "ISR", "country_name": "Israel"},
    ],
    "LBN": [
        {"iso3": "LBN", "country_name": "Lebanon"},
        {"iso3": "ISR", "country_name": "Israel"},
    ],
    "RUS": [
        {"iso3": "UKR", "country_name": "Ukraine"},
        {"iso3": "RUS", "country_name": "Russia"},
    ],
    "TWN": [
        {"iso3": "TWN", "country_name": "Taiwan"},
        {"iso3": "CHN", "country_name": "China"},
    ],
    "UKR": [
        {"iso3": "UKR", "country_name": "Ukraine"},
        {"iso3": "RUS", "country_name": "Russia"},
    ],
}


def _empty_report_inputs() -> pd.DataFrame:
    return pd.DataFrame(columns=REPORT_INPUT_COLUMNS)


def _as_date(value: object) -> date:
    return pd.Timestamp(value).date()


def _as_int(value: object, default: int = 0) -> int:
    if pd.isna(value):
        return default
    return int(value)


def _as_float(value: object, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    return float(value)


def _event_phrase(count: int, label: str) -> str:
    suffix = "" if count == 1 else "s"
    return f"{count} {label}{suffix}"


def _latest_country_week_rows(country_week_features: pd.DataFrame) -> pd.DataFrame:
    if country_week_features.empty:
        return country_week_features.copy()
    weekly = country_week_features.copy()
    weekly["week_start_date"] = pd.to_datetime(weekly["week_start_date"], errors="coerce")
    weekly = weekly.sort_values(["country_iso3", "week_start_date"]).reset_index(drop=True)
    latest = weekly.groupby("country_iso3", group_keys=False, sort=True).tail(1)
    return latest.sort_values("country_iso3").reset_index(drop=True)


def _country_week_with_scores(country_week_features: pd.DataFrame) -> pd.DataFrame:
    if country_week_features.empty:
        return country_week_features.copy()
    weekly = country_week_features.copy()
    weekly["week_start_date"] = pd.to_datetime(weekly["week_start_date"], errors="coerce")
    weekly["risk_score"] = weekly.apply(risk_score_from_country_week_row, axis=1)
    return weekly.sort_values(["country_iso3", "week_start_date"]).reset_index(drop=True)


def latest_label_targets_are_known(row: pd.Series) -> bool:
    return all(not pd.isna(row.get(column)) for column in ("label_escalation_7d", "label_escalation_30d", "label_onset_30d"))


def risk_score_from_country_week_row(row: pd.Series) -> float | None:
    if not latest_label_targets_are_known(row):
        return None
    score = (
        (_as_int(row.get("label_escalation_30d")) * 0.1)
        + (_as_int(row.get("label_escalation_7d")) * 0.1)
        + (_as_int(row.get("label_onset_30d")) * 0.05)
        + (min(_as_int(row.get("acled_event_count_28d")), 10) / 50.0)
        + (min(_as_int(row.get("gdelt_event_count_7d")), 20) / 200.0)
        + (min(_as_float(row.get("food_price_index")), 200.0) / 1000.0)
    )
    return round(min(score, 1.0), 2)


def risk_level_from_score(score: float) -> str:
    if score >= 0.6:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"


def top_driver_strings_from_row(row: pd.Series) -> list[str]:
    return [
        f"ACLED events (28d): {_as_int(row.get('acled_event_count_28d'))}",
        f"GDELT events (7d): {_as_int(row.get('gdelt_event_count_7d'))}",
        f"Food price index: {round(_as_float(row.get('food_price_index')), 1)}",
    ]


def summary_from_row(row: pd.Series, risk_level: str | object, risk_score: float | None) -> str:
    country_name = str(row["country_name"])
    acled_28d = _as_int(row.get("acled_event_count_28d"))
    gdelt_7d = _as_int(row.get("gdelt_event_count_7d"))
    food_price_index = round(_as_float(row.get("food_price_index")), 1)
    if risk_score is None or pd.isna(risk_level):
        return (
            f"{country_name} remains on the current monitoring board because the latest weekly signals show "
            f"{_event_phrase(acled_28d, 'ACLED event')} over 28 days, {_event_phrase(gdelt_7d, 'GDELT event')} over 7 days, "
            f"and a food price index of {food_price_index}."
        )
    return (
        f"{country_name} is in the {risk_level} monitoring band after {_event_phrase(acled_28d, 'ACLED event')} over 28 days, "
        f"{_event_phrase(gdelt_7d, 'GDELT event')} over 7 days, and a food price index of {food_price_index}."
    )


def chronology_strings_from_row(row: pd.Series) -> list[str]:
    week_start_date = _as_date(row["week_start_date"]).isoformat()
    return [
        f"Week of {week_start_date}: {_as_int(row.get('acled_event_count_7d'))} ACLED events in the trailing 7 days.",
        f"Trailing 28-day ACLED events: {_as_int(row.get('acled_event_count_28d'))}.",
        f"GDELT event count in the trailing 7 days: {_as_int(row.get('gdelt_event_count_7d'))}.",
    ]


def source_snapshot_hash_from_row(row: pd.Series) -> str:
    payload = {
        "country_iso3": row.get("country_iso3"),
        "week_start_date": str(row.get("week_start_date")),
        "snapshot_ts_utc": str(row.get("snapshot_ts_utc")),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def predicted_conflict_from_row(row: pd.Series) -> tuple[str, list[dict[str, str]], str]:
    iso3 = str(row["country_iso3"]).upper()
    curated = CURATED_CONFLICTS_BY_ISO3.get(iso3)
    if curated:
        label = " / ".join(item["country_name"] for item in curated)
        return label, curated, "report_inputs"

    label = str(row["country_name"])
    return (
        label,
        [
            {
                "iso3": iso3,
                "country_name": str(row["country_name"]),
            }
        ],
        "report_inputs",
    )


def build_gold_report_inputs(country_week_features: pd.DataFrame) -> pd.DataFrame:
    if country_week_features.empty:
        return _empty_report_inputs()

    latest_rows = _latest_country_week_rows(country_week_features)
    latest_rows = _country_week_with_scores(latest_rows)
    reports: list[dict[str, object]] = []

    for _, row in latest_rows.iterrows():
        report_date = _as_date(pd.Timestamp(row["week_start_date"]) + pd.Timedelta(days=6))
        risk_score = None if pd.isna(row["risk_score"]) else float(row["risk_score"])
        risk_level = risk_level_from_score(risk_score) if risk_score is not None else pd.NA
        top_drivers = top_driver_strings_from_row(row)
        chronology = chronology_strings_from_row(row)
        slug = f"{str(row['country_iso3']).lower()}-latest"
        summary = summary_from_row(row, risk_level, risk_score)
        predicted_conflict_label, predicted_conflict_countries, reason_source = predicted_conflict_from_row(row)
        narrative = maybe_generate_country_narrative(
            country_name=str(row["country_name"]),
            predicted_conflict_label=predicted_conflict_label,
            region_name=None if pd.isna(row.get("region_name")) else str(row.get("region_name")),
            forecast_target="label_escalation_30d",
            horizon_days=30,
            risk_level=None if pd.isna(risk_level) else str(risk_level),
            forecast_probability=risk_score,
            summary_fallback=summary,
            social_summary_fallback=summary,
            social_headline_fallback=f"{row['country_name']} monitoring update",
            social_body_fallback=summary,
            top_drivers=top_drivers,
            chronology=chronology,
        )
        reports.append(
            {
                "report_id": f"report-{slug}",
                "report_slug": slug,
                "report_title": f"{row['country_name']} Weekly Risk Brief",
                "country_iso3": row["country_iso3"],
                "country_name": row["country_name"],
                "region_name": row.get("region_name"),
                "report_date": report_date,
                "as_of_date": report_date,
                "forecast_horizon_days": 30,
                "forecast_target": "label_escalation_30d",
                "forecast_probability": risk_score,
                "risk_level": risk_level,
                "freshness_days": 6,
                "summary": narrative.report_summary if narrative is not None else summary,
                "predicted_conflict_label": predicted_conflict_label,
                "predicted_conflict_countries": json.dumps(predicted_conflict_countries),
                "reason_source": reason_source,
                "chronology": json.dumps(chronology),
                "top_drivers": json.dumps(top_drivers),
                "top_drivers_json": json.dumps(top_drivers),
                "source_snapshot_hash": source_snapshot_hash_from_row(row),
                "snapshot_ts_utc": row["snapshot_ts_utc"],
            }
        )

    report_inputs = pd.DataFrame.from_records(reports)
    return report_inputs[REPORT_INPUT_COLUMNS]
