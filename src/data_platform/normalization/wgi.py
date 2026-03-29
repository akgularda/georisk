from __future__ import annotations

import pandas as pd


WGI_COMPONENT_COLUMNS = {
    "voice_and_accountability": "governance_voice_and_accountability",
    "political_stability_and_absence_of_violence": "governance_political_stability",
    "government_effectiveness": "governance_government_effectiveness",
    "regulatory_quality": "governance_regulatory_quality",
    "rule_of_law": "governance_rule_of_law",
    "control_of_corruption": "governance_control_of_corruption",
}


def _ensure_utc_timestamp(value: pd.Timestamp | str | None) -> pd.Timestamp | pd.NaT:
    if value is None or pd.isna(value):
        return pd.NaT
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def normalize_wgi_snapshot(frame: pd.DataFrame, *, ingested_at: pd.Timestamp) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["country_iso3"] = normalized["country_iso3"].astype("string").str.upper().str.strip()
    normalized["country_name"] = normalized["country_name"].astype("string").str.strip()
    normalized["year"] = pd.to_numeric(normalized["year"], errors="coerce").astype("Int64")
    for source_column, target_column in WGI_COMPONENT_COLUMNS.items():
        normalized[target_column] = pd.to_numeric(normalized[source_column], errors="coerce")
    component_columns = list(WGI_COMPONENT_COLUMNS.values())
    normalized["governance_score"] = normalized[component_columns].mean(axis=1)
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
    normalized["source_name"] = "wgi"
    normalized["source_record_id"] = normalized["country_iso3"].astype("string") + "-" + normalized["year"].astype("string")
    normalized = normalized.loc[normalized["country_iso3"].notna() & normalized["year"].notna()].copy()
    return normalized[
        [
            "source_name",
            "source_record_id",
            "country_iso3",
            "country_name",
            "year",
            "governance_voice_and_accountability",
            "governance_political_stability",
            "governance_government_effectiveness",
            "governance_regulatory_quality",
            "governance_rule_of_law",
            "governance_control_of_corruption",
            "governance_score",
            "publication_ts_utc",
            "ingestion_ts_utc",
        ]
    ]
