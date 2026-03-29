from __future__ import annotations

import pandas as pd

from src.data_platform.countries import normalize_country_name_to_iso3


def normalize_ucdp_onset_dataset(
    frame: pd.DataFrame,
    *,
    onset_type: str,
    ingested_at: pd.Timestamp,
) -> pd.DataFrame:
    normalized = frame.copy()
    conflict_ids_column = next((column for column in normalized.columns if "conflict_ids" in column), "conflict_ids")
    normalized["country_name"] = normalized["name"].astype("string")
    normalized["country_iso3"] = normalized["country_name"].map(normalize_country_name_to_iso3)
    normalized["year"] = pd.to_numeric(normalized["year"], errors="coerce").astype("Int64")
    normalized["newconf"] = pd.to_numeric(normalized["newconf"], errors="coerce").fillna(0).astype("Int64")
    normalized["year_prev"] = pd.to_numeric(normalized["year_prev"], errors="coerce").astype("Int64")
    normalized["conflict_ids"] = normalized[conflict_ids_column].astype("string").str.strip()
    normalized.loc[normalized["conflict_ids"] == "", "conflict_ids"] = pd.NA
    for column in ["onset1", "onset2", "onset3", "onset5", "onset10", "onset20"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0).astype("Int64")
    normalized["source_name"] = "ucdp_onset"
    normalized["onset_type"] = onset_type
    normalized["ingestion_ts_utc"] = pd.Timestamp(ingested_at).tz_convert("UTC")
    normalized = normalized.loc[normalized["country_iso3"].notna() & normalized["year"].notna()].copy()
    return normalized[
        [
            "source_name",
            "onset_type",
            "country_iso3",
            "country_name",
            "year",
            "newconf",
            "onset1",
            "onset2",
            "onset3",
            "onset5",
            "onset10",
            "onset20",
            "conflict_ids",
            "year_prev",
            "ingestion_ts_utc",
        ]
    ]
