from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import pycountry


COUNTRY_NAME_OVERRIDES = {
    "Bolivia": "Bolivia, Plurinational State of",
    "Cape Verde": "Cabo Verde",
    "Congo-Kinshasa": "Congo, The Democratic Republic of the",
    "Congo-Brazzaville": "Congo",
    "Czech Republic": "Czechia",
    "Iran": "Iran, Islamic Republic of",
    "Kosovo": None,
    "Laos": "Lao People's Democratic Republic",
    "Moldova": "Moldova, Republic of",
    "North Korea": "Korea, Democratic People's Republic of",
    "Palestine": "Palestine, State of",
    "Russia": "Russian Federation",
    "South Korea": "Korea, Republic of",
    "Syria": "Syrian Arab Republic",
    "Taiwan": "Taiwan, Province of China",
    "Tanzania": "Tanzania, United Republic of",
    "Turkey": "Turkey",
    "Türkiye": "Turkey",
    "Venezuela": "Venezuela, Bolivarian Republic of",
}

COUNTRY_ISO3_NAME_OVERRIDES = {
    "IRN": "Iran",
    "PRK": "North Korea",
    "KOR": "South Korea",
    "RUS": "Russia",
    "SYR": "Syria",
    "TUR": "Turkey",
    "TWN": "Taiwan",
    "VEN": "Venezuela",
}

COUNTRY_REGION_OVERRIDES = {
    "AFG": "Asia",
    "ALB": "Europe",
    "AND": "Europe",
    "AGO": "Africa",
    "AIA": "Americas",
    "ARG": "Americas",
    "ARM": "Asia",
    "COL": "Americas",
    "DZA": "Africa",
    "EGY": "Africa",
    "IRN": "Asia",
    "ISR": "Asia",
    "SDN": "Africa",
    "SYR": "Asia",
    "TUR": "Asia",
    "UKR": "Europe",
}


def normalize_country_name_to_iso3(country_name: object | None) -> str | None:
    if country_name is None or pd.isna(country_name):
        return None
    normalized_input = str(country_name).strip()
    if not normalized_input:
        return None
    normalized_name = COUNTRY_NAME_OVERRIDES.get(normalized_input, normalized_input)
    if normalized_name is None:
        return None
    try:
        return pycountry.countries.lookup(normalized_name).alpha_3
    except LookupError:
        return None


def country_name_from_iso3(country_iso3: str | None) -> str | None:
    if country_iso3 is None or pd.isna(country_iso3):
        return None
    normalized_iso3 = str(country_iso3).strip().upper()
    if not normalized_iso3:
        return None
    override = COUNTRY_ISO3_NAME_OVERRIDES.get(normalized_iso3)
    if override is not None:
        return override
    country = pycountry.countries.get(alpha_3=normalized_iso3)
    if country is None:
        return None
    return getattr(country, "common_name", None) or getattr(country, "name", None)


def region_name_from_iso3(country_iso3: str | None) -> str | None:
    if country_iso3 is None or pd.isna(country_iso3):
        return None
    normalized_iso3 = str(country_iso3).strip().upper()
    if not normalized_iso3:
        return None
    return COUNTRY_REGION_OVERRIDES.get(normalized_iso3)


def extract_country_name_from_full_name(full_name: str | None) -> str | None:
    if full_name is None or pd.isna(full_name) or not str(full_name).strip():
        return None
    segments = [segment.strip() for segment in str(full_name).split(",") if segment.strip()]
    return segments[-1] if segments else None


def unique_non_null(values: Iterable[str | None]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value is None or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
