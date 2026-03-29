from __future__ import annotations

import pandas as pd


def _ensure_utc_timestamp(value: pd.Timestamp | str | None) -> pd.Timestamp | pd.NaT:
    if value is None or pd.isna(value):
        return pd.NaT
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def normalize_sipri_snapshot(
    frame: pd.DataFrame,
    *,
    ingested_at: pd.Timestamp,
    publication_ts_utc: pd.Timestamp | str | None = None,
) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["country_iso3"] = normalized["country_iso3"].astype("string").str.upper().str.strip()
    normalized["country_name"] = normalized["country_name"].astype("string").str.strip()
    normalized["year"] = pd.to_numeric(normalized["year"], errors="coerce").astype("Int64")
    for column in [
        "security_military_expenditure_usd",
        "security_military_expenditure_pct_gdp",
        "security_arms_import_volume_index",
    ]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    publication_value = publication_ts_utc if publication_ts_utc is not None and not pd.isna(publication_ts_utc) else pd.Timestamp.utcnow()
    normalized["publication_ts_utc"] = _ensure_utc_timestamp(publication_value)
    ingestion_ts = pd.Timestamp(ingested_at)
    if ingestion_ts.tzinfo is None:
        ingestion_ts = ingestion_ts.tz_localize("UTC")
    else:
        ingestion_ts = ingestion_ts.tz_convert("UTC")
    normalized["ingestion_ts_utc"] = ingestion_ts
    normalized["source_name"] = "sipri"
    normalized["source_record_id"] = normalized["country_iso3"].astype("string") + "-" + normalized["year"].astype("string")
    normalized = normalized.loc[normalized["country_iso3"].notna() & normalized["year"].notna()].copy()
    return normalized[
        [
            "source_name",
            "source_record_id",
            "country_iso3",
            "country_name",
            "year",
            "security_military_expenditure_usd",
            "security_military_expenditure_pct_gdp",
            "security_arms_import_volume_index",
            "publication_ts_utc",
            "ingestion_ts_utc",
        ]
    ].sort_values(by=["country_iso3", "year"])
