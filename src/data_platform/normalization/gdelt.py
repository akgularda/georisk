from __future__ import annotations

import json

import pandas as pd

from src.data_platform.countries import extract_country_name_from_full_name, normalize_country_name_to_iso3, unique_non_null


def normalize_gdelt_events(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["event_date"] = pd.to_datetime(normalized["sql_date"], format="%Y%m%d", errors="coerce").dt.date
    normalized["published_at"] = pd.to_datetime(normalized["date_added"], format="%Y%m%d%H%M%S", errors="coerce", utc=True)
    normalized["source_country_name"] = normalized["action_geo_full_name"].map(extract_country_name_from_full_name)
    normalized["country_id"] = normalized["source_country_name"].map(normalize_country_name_to_iso3)
    numeric_columns = ["goldstein_scale", "num_mentions", "num_sources", "num_articles", "avg_tone", "action_geo_lat", "action_geo_long"]
    for column in numeric_columns:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    return normalized[
        [
            "global_event_id",
            "event_date",
            "published_at",
            "country_id",
            "source_country_name",
            "action_geo_country_code",
            "action_geo_full_name",
            "event_code",
            "event_base_code",
            "event_root_code",
            "quad_class",
            "goldstein_scale",
            "num_mentions",
            "num_sources",
            "num_articles",
            "avg_tone",
            "source_url",
        ]
    ]


def _extract_location_entries(v2_locations: str | None) -> list[dict[str, str | None]]:
    if v2_locations is None or pd.isna(v2_locations) or not str(v2_locations).strip():
        return []
    entries: list[dict[str, str | None]] = []
    for raw_entry in str(v2_locations).split(";"):
        if not raw_entry:
            continue
        parts = raw_entry.split("#")
        if len(parts) < 4:
            continue
        entries.append(
            {
                "geo_type": parts[0],
                "location_name": parts[1] or None,
                "country_code": parts[2] or None,
                "adm1_code": parts[3] or None,
            }
        )
    return entries


def normalize_gdelt_gkg_documents(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["published_at"] = pd.to_datetime(normalized["date"], format="%Y%m%d%H%M%S", errors="coerce", utc=True)
    normalized["document_date"] = normalized["published_at"].dt.date
    normalized["tone_score"] = normalized["v2_tone"].fillna("").map(
        lambda raw: float(raw.split(",")[0]) if raw and raw.split(",")[0] not in {"", None} else None
    )

    records: list[dict[str, object]] = []
    for row in normalized.to_dict(orient="records"):
        locations = _extract_location_entries(row.get("v2_locations"))
        location_codes = unique_non_null(
            normalize_country_name_to_iso3(
                location["location_name"]
                if location.get("geo_type") == "1"
                else extract_country_name_from_full_name(location.get("location_name"))
            )
            for location in locations
        )
        if not location_codes:
            location_codes = unique_non_null(
                normalize_country_name_to_iso3(extract_country_name_from_full_name(location.get("location_name")))
                for location in locations
            )
        if not location_codes and row.get("source_common_name"):
            location_codes = []

        if not location_codes:
            records.append(
                {
                    "gkg_record_id": row["gkg_record_id"],
                    "document_identifier": row["document_identifier"],
                    "document_date": row["document_date"],
                    "published_at": row["published_at"],
                    "document_country_id": None,
                    "source_common_name": row["source_common_name"],
                    "themes": row["themes"],
                    "v2_themes": row["v2_themes"],
                    "tone_score": row["tone_score"],
                }
            )
            continue

        for country_id in location_codes:
            records.append(
                {
                    "gkg_record_id": row["gkg_record_id"],
                    "document_identifier": row["document_identifier"],
                    "document_date": row["document_date"],
                    "published_at": row["published_at"],
                    "document_country_id": country_id,
                    "source_common_name": row["source_common_name"],
                    "themes": row["themes"],
                    "v2_themes": row["v2_themes"],
                    "tone_score": row["tone_score"],
                }
            )
    return pd.DataFrame(records)
