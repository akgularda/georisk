from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from src.data_platform.countries import country_name_from_iso3, region_name_from_iso3


def _normalize_week_start(value: pd.Timestamp | str | object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert("UTC").tz_localize(None)
    return timestamp.normalize() - pd.Timedelta(days=timestamp.normalize().weekday())


def _first_present_value(series: pd.Series) -> str | pd.NAType:
    for value in series:
        if value is None or pd.isna(value):
            continue
        normalized = str(value).strip()
        if normalized:
            return normalized
    return pd.NA


def build_weekly_date_index(
    start_date: pd.Timestamp | str | object,
    end_date: pd.Timestamp | str | object,
) -> pd.DataFrame:
    start_week = _normalize_week_start(start_date)
    end_week = _normalize_week_start(end_date)
    if end_week < start_week:
        raise ValueError("end_date must be on or after start_date")
    return pd.DataFrame({"week_start_date": pd.date_range(start_week, end_week, freq="W-MON")})


def build_country_dimension(
    country_iso3_values: Iterable[str | None],
    *,
    metadata_frames: Iterable[pd.DataFrame] = (),
) -> pd.DataFrame:
    country_iso3 = (
        pd.Series(list(country_iso3_values), dtype="string")
        .dropna()
        .str.upper()
        .str.strip()
    )
    country_iso3 = country_iso3.loc[country_iso3.str.fullmatch(r"[A-Z]{3}")]
    if country_iso3.empty:
        return pd.DataFrame(columns=["country_iso3", "country_name", "region_name"])

    dimension = pd.DataFrame({"country_iso3": country_iso3.drop_duplicates().sort_values().tolist()})

    metadata_parts: list[pd.DataFrame] = []
    for frame in metadata_frames:
        if frame.empty or "country_iso3" not in frame.columns:
            continue
        available_columns = ["country_iso3"]
        if "country_name" in frame.columns:
            available_columns.append("country_name")
        if "region_name" in frame.columns:
            available_columns.append("region_name")
        metadata = frame.loc[frame["country_iso3"].notna(), available_columns].copy()
        metadata["country_iso3"] = metadata["country_iso3"].astype("string").str.upper().str.strip()
        if "country_name" not in metadata.columns:
            metadata["country_name"] = pd.NA
        if "region_name" not in metadata.columns:
            metadata["region_name"] = pd.NA
        metadata_parts.append(metadata[["country_iso3", "country_name", "region_name"]])

    if metadata_parts:
        resolved = (
            pd.concat(metadata_parts, ignore_index=True)
            .groupby("country_iso3", dropna=False)
            .agg(
                country_name=("country_name", _first_present_value),
                region_name=("region_name", _first_present_value),
            )
            .reset_index()
        )
        dimension = dimension.merge(resolved, on="country_iso3", how="left")
    else:
        dimension["country_name"] = pd.NA
        dimension["region_name"] = pd.NA

    dimension["country_name"] = dimension.apply(
        lambda row: row["country_name"] if pd.notna(row["country_name"]) else country_name_from_iso3(row["country_iso3"]),
        axis=1,
    )
    dimension["region_name"] = dimension.apply(
        lambda row: row["region_name"] if pd.notna(row["region_name"]) else region_name_from_iso3(row["country_iso3"]),
        axis=1,
    )
    return dimension.astype({"country_iso3": "string", "country_name": "string", "region_name": "string"})


def build_country_week_panel(country_dimension: pd.DataFrame, weekly_date_index: pd.DataFrame) -> pd.DataFrame:
    if country_dimension.empty or weekly_date_index.empty:
        return pd.DataFrame(columns=["country_iso3", "country_name", "region_name", "week_start_date"])
    return (
        country_dimension.merge(weekly_date_index, how="cross")
        .sort_values(by=["country_iso3", "week_start_date"])
        .reset_index(drop=True)
    )
