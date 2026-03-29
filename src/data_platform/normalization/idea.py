from __future__ import annotations

import pandas as pd


def _ensure_utc_timestamp(value: pd.Timestamp | str | None) -> pd.Timestamp | pd.NaT:
    if value is None or pd.isna(value):
        return pd.NaT
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def normalize_idea_election_calendar(frame: pd.DataFrame, *, ingested_at: pd.Timestamp) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["country_iso3"] = normalized["country_iso3"].astype("string").str.upper().str.strip()
    normalized["country_name"] = normalized["country_name"].astype("string").str.strip()
    normalized["election_date"] = pd.to_datetime(normalized["election_date"], errors="coerce").dt.normalize()
    for column in ["election_type", "election_name", "status"]:
        if column not in normalized.columns:
            normalized[column] = None
        normalized[column] = normalized[column].astype("string").str.strip()
    if "publication_ts_utc" in normalized.columns:
        normalized["publication_ts_utc"] = normalized["publication_ts_utc"].map(_ensure_utc_timestamp)
    else:
        normalized["publication_ts_utc"] = pd.NaT
    ingestion_ts = pd.Timestamp(ingested_at)
    if ingestion_ts.tzinfo is None:
        ingestion_ts = ingestion_ts.tz_localize("UTC")
    else:
        ingestion_ts = ingestion_ts.tz_convert("UTC")
    normalized["ingestion_ts_utc"] = ingestion_ts
    normalized["source_name"] = "idea"
    normalized = normalized.loc[normalized["country_iso3"].notna() & normalized["election_date"].notna()].copy()
    election_type_slug = normalized["election_type"].fillna("unknown").str.lower().str.replace(r"[^a-z0-9]+", "_", regex=True).str.strip("_")
    normalized["source_record_id"] = (
        normalized["country_iso3"].astype("string") + "-" + normalized["election_date"].dt.strftime("%Y-%m-%d") + "-" + election_type_slug
    )
    return normalized[
        [
            "source_name",
            "source_record_id",
            "country_iso3",
            "country_name",
            "election_date",
            "election_type",
            "election_name",
            "status",
            "publication_ts_utc",
            "ingestion_ts_utc",
        ]
    ]
