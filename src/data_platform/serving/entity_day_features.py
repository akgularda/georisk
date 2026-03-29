from __future__ import annotations

import hashlib
import json

import pandas as pd


ENTITY_DAY_FEATURE_COLUMNS = [
    "entity_id",
    "entity_name",
    "entity_type",
    "country_iso3",
    "country_name",
    "region_name",
    "feature_date",
    "source_week_start_date",
    "acled_event_count_7d",
    "acled_event_count_28d",
    "gdelt_event_count_7d",
    "food_price_index",
    "macro_cpi_yoy",
    "climate_drought_severity_index",
    "snapshot_ts_utc",
    "feature_snapshot_hash",
]


def _empty_entity_day_features() -> pd.DataFrame:
    return pd.DataFrame(columns=ENTITY_DAY_FEATURE_COLUMNS)


def _feature_snapshot_hash(row: pd.Series, feature_date: object) -> str:
    payload = {
        "country_iso3": row.get("country_iso3"),
        "week_start_date": str(row.get("week_start_date")),
        "feature_date": str(feature_date),
        "snapshot_ts_utc": str(row.get("snapshot_ts_utc")),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def build_gold_entity_day_features(country_week_features: pd.DataFrame) -> pd.DataFrame:
    if country_week_features.empty:
        return _empty_entity_day_features()

    weekly = country_week_features.copy()
    weekly["week_start_date"] = pd.to_datetime(weekly["week_start_date"], errors="coerce")
    records: list[dict[str, object]] = []

    for _, row in weekly.iterrows():
        for day_offset in range(7):
            feature_date = (pd.Timestamp(row["week_start_date"]) + pd.Timedelta(days=day_offset)).date()
            records.append(
                {
                    "entity_id": row["country_iso3"],
                    "entity_name": row["country_name"],
                    "entity_type": "country",
                    "country_iso3": row["country_iso3"],
                    "country_name": row["country_name"],
                    "region_name": row.get("region_name"),
                    "feature_date": feature_date,
                    "source_week_start_date": pd.Timestamp(row["week_start_date"]).date(),
                    "acled_event_count_7d": row.get("acled_event_count_7d"),
                    "acled_event_count_28d": row.get("acled_event_count_28d"),
                    "gdelt_event_count_7d": row.get("gdelt_event_count_7d"),
                    "food_price_index": row.get("food_price_index"),
                    "macro_cpi_yoy": row.get("macro_cpi_yoy"),
                    "climate_drought_severity_index": row.get("climate_drought_severity_index"),
                    "snapshot_ts_utc": row.get("snapshot_ts_utc"),
                    "feature_snapshot_hash": _feature_snapshot_hash(row, feature_date),
                }
            )

    entity_day_features = pd.DataFrame.from_records(records).sort_values(["country_iso3", "feature_date"]).reset_index(drop=True)
    return entity_day_features[ENTITY_DAY_FEATURE_COLUMNS]
