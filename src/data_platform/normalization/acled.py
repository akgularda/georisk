from __future__ import annotations

import io
import re

import pandas as pd

from src.data_platform.countries import normalize_country_name_to_iso3


def _slugify_event_type(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    slug = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    return slug or None


def _first_present(row: pd.Series, *column_names: str) -> object:
    for column_name in column_names:
        if column_name in row and not pd.isna(row[column_name]) and str(row[column_name]).strip():
            return row[column_name]
    return None


def normalize_acled_events(frame: pd.DataFrame, *, ingested_at: pd.Timestamp) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["source_record_id"] = normalized.apply(
        lambda row: _first_present(row, "event_id_cnty", "data_id", "event_id_no_cnty"),
        axis=1,
    )
    normalized["country_iso3"] = normalized["country"].map(normalize_country_name_to_iso3)
    normalized["event_date"] = pd.to_datetime(normalized["event_date"], errors="coerce").dt.normalize()
    if "timestamp" in normalized.columns:
        normalized["publication_ts_utc"] = pd.to_datetime(normalized["timestamp"], errors="coerce", utc=True)
    else:
        normalized["publication_ts_utc"] = pd.Series(pd.NaT, index=normalized.index, dtype="datetime64[ns, UTC]")
    ingestion_ts = pd.Timestamp(ingested_at)
    if ingestion_ts.tzinfo is None:
        ingestion_ts = ingestion_ts.tz_localize("UTC")
    else:
        ingestion_ts = ingestion_ts.tz_convert("UTC")
    normalized["ingestion_ts_utc"] = ingestion_ts
    normalized["event_type"] = normalized["event_type"].astype("string")
    normalized["sub_event_type"] = normalized["sub_event_type"].astype("string")
    normalized["event_type_slug"] = normalized["event_type"].map(_slugify_event_type)
    normalized["sub_event_type_slug"] = normalized["sub_event_type"].map(_slugify_event_type)

    text_columns = ["actor1", "assoc_actor_1", "actor2", "assoc_actor_2", "notes", "admin1", "admin2", "location"]
    for column in text_columns:
        if column in normalized.columns:
            normalized[column] = normalized[column].map(lambda value: None if pd.isna(value) else str(value).strip() or None)

    numeric_columns = ["fatalities", "latitude", "longitude", "geo_precision", "time_precision", "year"]
    for column in numeric_columns:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    for column in ["location", "assoc_actor_1", "assoc_actor_2", "source"]:
        if column not in normalized.columns:
            normalized[column] = None

    normalized = normalized.loc[normalized["country_iso3"].notna() & normalized["event_date"].notna()].copy()
    normalized["source_name"] = "acled"
    return normalized[
        [
            "source_name",
            "source_record_id",
            "country_iso3",
            "country",
            "admin1",
            "admin2",
            "location",
            "event_date",
            "publication_ts_utc",
            "ingestion_ts_utc",
            "event_type",
            "sub_event_type",
            "event_type_slug",
            "sub_event_type_slug",
            "actor1",
            "assoc_actor_1",
            "actor2",
            "assoc_actor_2",
            "fatalities",
            "notes",
            "latitude",
            "longitude",
            "source",
        ]
    ].rename(
        columns={
            "country": "country_name",
            "admin1": "admin1_name",
            "admin2": "admin2_name",
            "location": "location_name",
            "actor1": "actor1_name",
            "assoc_actor_1": "actor1_associated_actor_name",
            "actor2": "actor2_name",
            "assoc_actor_2": "actor2_associated_actor_name",
        }
    )
