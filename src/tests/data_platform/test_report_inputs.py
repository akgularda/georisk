from __future__ import annotations

import json

import pandas as pd

from src.data_platform.serving.report_inputs import ai_narrative_country_iso3s, build_gold_report_inputs


def test_build_gold_report_inputs_uses_latest_week_per_country() -> None:
    snapshot_ts = pd.Timestamp("2026-03-27T12:00:00Z")
    country_week_features = pd.DataFrame(
        {
            "country_iso3": ["USA", "USA", "FRA"],
            "country_name": ["United States", "United States", "France"],
            "region_name": ["North America", "North America", "Europe"],
            "week_start_date": [pd.Timestamp("2026-03-16"), pd.Timestamp("2026-03-23"), pd.Timestamp("2026-03-23")],
            "label_escalation_7d": [0, 1, 0],
            "label_escalation_30d": [0, 1, 0],
            "label_onset_30d": [0, 1, 0],
            "acled_event_count_7d": [1, 4, 0],
            "acled_event_count_28d": [3, 9, 1],
            "gdelt_event_count_7d": [8, 18, 2],
            "food_price_index": [120.5, 125.0, 110.0],
            "macro_cpi_yoy": [2.1, 3.4, 1.8],
            "climate_drought_severity_index": [0.1, 0.8, 0.0],
            "days_to_next_election": [50, 43, pd.NA],
            "snapshot_ts_utc": [snapshot_ts, snapshot_ts, snapshot_ts],
        }
    )

    report_inputs = build_gold_report_inputs(country_week_features)

    assert list(report_inputs["country_iso3"]) == ["FRA", "USA"]
    assert list(report_inputs["report_slug"]) == ["fra-latest", "usa-latest"]
    assert list(report_inputs["report_date"]) == [pd.Timestamp("2026-03-29").date(), pd.Timestamp("2026-03-29").date()]
    assert list(report_inputs["freshness_days"]) == [6, 6]

    usa_row = report_inputs.loc[report_inputs["country_iso3"] == "USA"].iloc[0]
    assert usa_row["risk_level"] == "high"
    assert usa_row["forecast_target"] == "label_escalation_30d"
    assert usa_row["forecast_horizon_days"] == 30
    assert (
        usa_row["summary"]
        == "United States is in the high monitoring band after 9 ACLED events over 28 days, 18 GDELT events over 7 days, and a food price index of 125.0."
    )
    assert usa_row["predicted_conflict_label"] == "United States"
    assert json.loads(usa_row["predicted_conflict_countries"]) == [{"iso3": "USA", "country_name": "United States"}]
    assert usa_row["reason_source"] == "report_inputs"

    chronology = json.loads(usa_row["chronology"])
    assert chronology == [
        "Week of 2026-03-23: 4 ACLED events in the trailing 7 days.",
        "Trailing 28-day ACLED events: 9.",
        "GDELT event count in the trailing 7 days: 18.",
    ]

    top_drivers = json.loads(usa_row["top_drivers"])
    assert top_drivers == [
        "ACLED events (28d): 9",
        "GDELT events (7d): 18",
        "Food price index: 125.0",
    ]


def test_build_gold_report_inputs_returns_empty_frame_for_empty_input() -> None:
    report_inputs = build_gold_report_inputs(pd.DataFrame())

    assert report_inputs.empty
    assert list(report_inputs.columns) == [
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


def test_build_gold_report_inputs_nulls_forecast_fields_when_latest_labels_are_unknown() -> None:
    snapshot_ts = pd.Timestamp("2026-03-27T12:00:00Z")
    country_week_features = pd.DataFrame(
        {
            "country_iso3": ["USA", "USA"],
            "country_name": ["United States", "United States"],
            "region_name": ["North America", "North America"],
            "week_start_date": [pd.Timestamp("2026-03-16"), pd.Timestamp("2026-03-23")],
            "label_escalation_7d": [0, pd.NA],
            "label_escalation_30d": [0, pd.NA],
            "label_onset_30d": [0, pd.NA],
            "acled_event_count_7d": [1, 4],
            "acled_event_count_28d": [3, 9],
            "gdelt_event_count_7d": [8, 18],
            "food_price_index": [120.5, 125.0],
            "macro_cpi_yoy": [2.1, 3.4],
            "climate_drought_severity_index": [0.1, 0.8],
            "snapshot_ts_utc": [snapshot_ts, snapshot_ts],
        }
    )

    report_inputs = build_gold_report_inputs(country_week_features)

    usa_row = report_inputs.iloc[0]
    assert pd.isna(usa_row["forecast_probability"])
    assert pd.isna(usa_row["risk_level"])
    assert (
        usa_row["summary"]
        == "United States remains on the current monitoring board because the latest weekly signals show 9 ACLED events over 28 days, 18 GDELT events over 7 days, and a food price index of 125.0."
    )

    chronology = json.loads(usa_row["chronology"])
    assert chronology == [
        "Week of 2026-03-23: 4 ACLED events in the trailing 7 days.",
        "Trailing 28-day ACLED events: 9.",
        "GDELT event count in the trailing 7 days: 18.",
    ]


def test_ai_narrative_country_iso3s_prefers_top_scores_and_curated_conflicts() -> None:
    latest_rows = pd.DataFrame(
        {
            "country_iso3": ["USA", "FRA", "IRN", "UKR", "BRA"],
            "risk_score": [0.9, 0.1, 0.2, None, 0.8],
        }
    )

    eligible = ai_narrative_country_iso3s(latest_rows, max_count=2)

    assert "USA" in eligible
    assert "BRA" in eligible
    assert "IRN" in eligible
    assert "UKR" in eligible
