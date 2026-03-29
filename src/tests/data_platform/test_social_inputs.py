from __future__ import annotations

import json

import pandas as pd

from src.data_platform.serving.social_inputs import build_gold_social_inputs


def test_build_gold_social_inputs_uses_latest_week_and_previous_delta() -> None:
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

    social_inputs = build_gold_social_inputs(country_week_features)

    assert list(social_inputs["country_iso3"]) == ["FRA", "USA"]
    assert list(social_inputs["report_slug"]) == ["fra-latest", "usa-latest"]
    assert list(social_inputs["publish_date"]) == [pd.Timestamp("2026-03-29").date(), pd.Timestamp("2026-03-29").date()]

    usa_row = social_inputs.loc[social_inputs["country_iso3"] == "USA"].iloc[0]
    assert usa_row["score_delta"] == 0.4
    assert (
        usa_row["summary_line"]
        == "United States moved into the high monitoring band after 9 ACLED events over 28 days and 18 GDELT events over 7 days."
    )
    assert usa_row["headline"] == "United States monitoring update: high"
    assert usa_row["call_to_action"] == "Review the latest country monitoring brief."
    assert usa_row["destination_url"] == "/countries/usa-latest"

    top_drivers = json.loads(usa_row["top_drivers"])
    assert top_drivers == [
        "ACLED events (28d): 9",
        "GDELT events (7d): 18",
        "Food price index: 125.0",
    ]

    fra_row = social_inputs.loc[social_inputs["country_iso3"] == "FRA"].iloc[0]
    assert fra_row["score_delta"] == 0.0


def test_build_gold_social_inputs_returns_empty_frame_for_empty_input() -> None:
    social_inputs = build_gold_social_inputs(pd.DataFrame())

    assert social_inputs.empty
    assert list(social_inputs.columns) == [
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


def test_build_gold_social_inputs_uses_neutral_copy_when_score_is_unchanged() -> None:
    snapshot_ts = pd.Timestamp("2026-03-27T12:00:00Z")
    country_week_features = pd.DataFrame(
        {
            "country_iso3": ["FRA", "FRA"],
            "country_name": ["France", "France"],
            "region_name": ["Europe", "Europe"],
            "week_start_date": [pd.Timestamp("2026-03-16"), pd.Timestamp("2026-03-23")],
            "label_escalation_7d": [0, 0],
            "label_escalation_30d": [0, 0],
            "label_onset_30d": [0, 0],
            "acled_event_count_7d": [0, 0],
            "acled_event_count_28d": [1, 1],
            "gdelt_event_count_7d": [2, 2],
            "food_price_index": [110.0, 110.0],
            "macro_cpi_yoy": [1.8, 1.8],
            "climate_drought_severity_index": [0.0, 0.0],
            "snapshot_ts_utc": [snapshot_ts, snapshot_ts],
        }
    )

    social_inputs = build_gold_social_inputs(country_week_features)

    fra_row = social_inputs.iloc[0]
    assert fra_row["score_delta"] == 0.0
    assert fra_row["summary_line"] == "France remains in the low monitoring band after 1 ACLED event over 28 days and 2 GDELT events over 7 days."
    assert fra_row["body"].startswith("France remains in the low monitoring band after 1 ACLED event over 28 days and 2 GDELT events over 7 days.")


def test_build_gold_social_inputs_uses_neutral_copy_when_score_changes_inside_same_risk_band() -> None:
    snapshot_ts = pd.Timestamp("2026-03-27T12:00:00Z")
    country_week_features = pd.DataFrame(
        {
            "country_iso3": ["FRA", "FRA"],
            "country_name": ["France", "France"],
            "region_name": ["Europe", "Europe"],
            "week_start_date": [pd.Timestamp("2026-03-16"), pd.Timestamp("2026-03-23")],
            "label_escalation_7d": [0, 0],
            "label_escalation_30d": [0, 0],
            "label_onset_30d": [0, 1],
            "acled_event_count_7d": [0, 0],
            "acled_event_count_28d": [1, 4],
            "gdelt_event_count_7d": [2, 4],
            "food_price_index": [110.0, 120.0],
            "macro_cpi_yoy": [1.8, 2.0],
            "climate_drought_severity_index": [0.0, 0.2],
            "snapshot_ts_utc": [snapshot_ts, snapshot_ts],
        }
    )

    social_inputs = build_gold_social_inputs(country_week_features)

    fra_row = social_inputs.iloc[0]
    assert fra_row["score_delta"] == 0.1
    assert fra_row["summary_line"] == "France remains in the low monitoring band after 4 ACLED events over 28 days and 4 GDELT events over 7 days."
    assert fra_row["body"].startswith("France remains in the low monitoring band after 4 ACLED events over 28 days and 4 GDELT events over 7 days.")


def test_build_gold_social_inputs_nulls_forecast_fields_when_latest_labels_are_unknown() -> None:
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

    social_inputs = build_gold_social_inputs(country_week_features)

    usa_row = social_inputs.iloc[0]
    assert pd.isna(usa_row["forecast_probability"])
    assert pd.isna(usa_row["score_delta"])
    assert (
        usa_row["summary_line"]
        == "United States remains on the current monitoring board. Latest signals show 9 ACLED events over 28 days and 18 GDELT events over 7 days."
    )
    assert usa_row["body"].startswith(
        "United States remains on the current monitoring board. Latest signals show 9 ACLED events over 28 days and 18 GDELT events over 7 days."
    )


def test_build_gold_social_inputs_handles_unknown_previous_score_without_crashing() -> None:
    snapshot_ts = pd.Timestamp("2026-03-27T12:00:00Z")
    country_week_features = pd.DataFrame(
        {
            "country_iso3": ["USA", "USA"],
            "country_name": ["United States", "United States"],
            "region_name": ["North America", "North America"],
            "week_start_date": [pd.Timestamp("2026-03-16"), pd.Timestamp("2026-03-23")],
            "label_escalation_7d": [pd.NA, 1],
            "label_escalation_30d": [pd.NA, 1],
            "label_onset_30d": [pd.NA, 1],
            "acled_event_count_7d": [1, 4],
            "acled_event_count_28d": [3, 9],
            "gdelt_event_count_7d": [8, 18],
            "food_price_index": [120.5, 125.0],
            "macro_cpi_yoy": [2.1, 3.4],
            "climate_drought_severity_index": [0.1, 0.8],
            "snapshot_ts_utc": [snapshot_ts, snapshot_ts],
        }
    )

    social_inputs = build_gold_social_inputs(country_week_features)

    usa_row = social_inputs.iloc[0]
    assert pd.isna(usa_row["score_delta"])
    assert usa_row["summary_line"] == "United States enters the high monitoring band after 9 ACLED events over 28 days and 18 GDELT events over 7 days."
    assert usa_row["headline"] == "United States monitoring update: high"
