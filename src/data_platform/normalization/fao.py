from __future__ import annotations

import pandas as pd


def _ensure_utc_timestamp(value: pd.Timestamp | str | None) -> pd.Timestamp | pd.NaT:
    if value is None or pd.isna(value):
        return pd.NaT
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def normalize_fao_snapshot(frame: pd.DataFrame, *, ingested_at: pd.Timestamp, publication_ts_utc: pd.Timestamp | str | None = None) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["observation_date"] = pd.to_datetime(normalized["observation_date"], errors="coerce").dt.normalize()
    for column in ["food_price_index", "food_cereal_price_index"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    publication_value = publication_ts_utc if publication_ts_utc is not None and not pd.isna(publication_ts_utc) else normalized["observation_date"].max()
    normalized["publication_ts_utc"] = _ensure_utc_timestamp(publication_value)
    ingestion_ts = pd.Timestamp(ingested_at)
    if ingestion_ts.tzinfo is None:
        ingestion_ts = ingestion_ts.tz_localize("UTC")
    else:
        ingestion_ts = ingestion_ts.tz_convert("UTC")
    normalized["ingestion_ts_utc"] = ingestion_ts
    normalized["source_name"] = "fao"
    normalized["source_record_id"] = normalized["observation_date"].dt.strftime("%Y-%m-%d")
    normalized = normalized.loc[normalized["observation_date"].notna()].copy()
    return normalized[
        [
            "source_name",
            "source_record_id",
            "observation_date",
            "food_price_index",
            "food_cereal_price_index",
            "publication_ts_utc",
            "ingestion_ts_utc",
        ]
    ].sort_values(by="observation_date")
