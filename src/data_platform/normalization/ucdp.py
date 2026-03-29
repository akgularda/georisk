from __future__ import annotations

import pandas as pd

from src.data_platform.countries import normalize_country_name_to_iso3


UCDP_TYPE_OF_VIOLENCE_MAP = {
    1: "state_based",
    2: "non_state",
    3: "one_sided",
}


def _extract_first_source_date(raw_value: object) -> pd.Timestamp | pd.NaT:
    if raw_value is None or pd.isna(raw_value):
        return pd.NaT
    first_value = str(raw_value).split(";")[0].strip()
    if not first_value:
        return pd.NaT
    return pd.to_datetime(first_value, errors="coerce", utc=True)


def normalize_ucdp_ged_events(frame: pd.DataFrame, *, ingested_at: pd.Timestamp) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["source_record_id"] = normalized["id"].astype(str)
    normalized["country_iso3"] = normalized["country"].map(normalize_country_name_to_iso3)
    normalized["event_date_start"] = pd.to_datetime(normalized["date_start"], errors="coerce").dt.normalize()
    normalized["event_date_end"] = pd.to_datetime(normalized["date_end"], errors="coerce").dt.normalize()
    normalized["publication_ts_utc"] = normalized["source_date"].map(_extract_first_source_date)
    normalized["ingestion_ts_utc"] = pd.Timestamp(ingested_at).tz_convert("UTC")
    normalized["event_type"] = pd.to_numeric(normalized["type_of_violence"], errors="coerce").map(UCDP_TYPE_OF_VIOLENCE_MAP)
    for column in ["best", "high", "low", "latitude", "longitude", "where_prec", "year"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    normalized = normalized.loc[normalized["country_iso3"].notna() & normalized["event_date_start"].notna()].copy()
    normalized["source_name"] = "ucdp_ged"
    return normalized[
        [
            "source_name",
            "source_record_id",
            "country_iso3",
            "country",
            "region",
            "adm_1",
            "adm_2",
            "event_date_start",
            "event_date_end",
            "publication_ts_utc",
            "ingestion_ts_utc",
            "event_type",
            "type_of_violence",
            "conflict_dset_id",
            "conflict_new_id",
            "conflict_name",
            "side_a",
            "side_b",
            "best",
            "high",
            "low",
            "latitude",
            "longitude",
            "where_prec",
            "year",
        ]
    ].rename(
        columns={
            "country": "country_name",
            "region": "region_name",
            "adm_1": "admin1_name",
            "adm_2": "admin2_name",
            "best": "best_fatalities",
            "high": "high_fatalities",
            "low": "low_fatalities",
            "where_prec": "location_precision",
        }
    )
