from __future__ import annotations

import pandas as pd


WDI_INDICATOR_COLUMN_MAP = {
    "NY.GDP.MKTP.KD.ZG": "macro_gdp_growth_annual_pct",
    "FP.CPI.TOTL.ZG": "macro_cpi_yoy",
    "SP.POP.TOTL": "macro_population_total",
}


def normalize_wdi_indicator_series(
    frame: pd.DataFrame,
    metadata: dict[str, object],
    *,
    ingested_at: pd.Timestamp,
) -> pd.DataFrame:
    normalized = frame.copy()
    normalized = normalized.loc[
        normalized["countryiso3code"].notna()
        & normalized["countryiso3code"].astype(str).str.fullmatch(r"[A-Z]{3}")
    ].copy()
    normalized["country_iso3"] = normalized["countryiso3code"]
    normalized["country_name"] = normalized["country"].map(lambda raw: raw.get("value") if isinstance(raw, dict) else None)
    normalized["indicator_id"] = normalized["indicator"].map(lambda raw: raw.get("id") if isinstance(raw, dict) else None)
    normalized["indicator_name"] = normalized["indicator"].map(
        lambda raw: raw.get("value") if isinstance(raw, dict) else None
    )
    normalized["year"] = pd.to_numeric(normalized["date"], errors="coerce").astype("Int64")
    normalized["value"] = pd.to_numeric(normalized["value"], errors="coerce")
    normalized["publication_ts_utc"] = pd.Timestamp(str(metadata.get("lastupdated")), tz="UTC")
    normalized["ingestion_ts_utc"] = pd.Timestamp(ingested_at).tz_convert("UTC")
    normalized["frequency"] = "annual"
    normalized["source_name"] = "world_bank_wdi"
    return normalized[
        [
            "source_name",
            "country_iso3",
            "country_name",
            "indicator_id",
            "indicator_name",
            "year",
            "value",
            "frequency",
            "publication_ts_utc",
            "ingestion_ts_utc",
        ]
    ].sort_values(by=["country_iso3", "indicator_id", "year"], ascending=[True, True, False])


def pivot_wdi_indicator_snapshot(frame: pd.DataFrame) -> pd.DataFrame:
    pivoted = (
        frame.pivot_table(
            index=["country_iso3", "country_name", "year"],
            columns="indicator_id",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns=WDI_INDICATOR_COLUMN_MAP)
    )
    lineage = frame.groupby(["country_iso3", "country_name", "year"], dropna=False).agg(
        publication_ts_utc=("publication_ts_utc", "max"),
        ingestion_ts_utc=("ingestion_ts_utc", "max"),
    )
    return (
        pivoted.merge(
            lineage.reset_index(),
            on=["country_iso3", "country_name", "year"],
            how="left",
        )
        .sort_values(by=["country_iso3", "year"], ascending=[True, False])
        .reset_index(drop=True)
    )
