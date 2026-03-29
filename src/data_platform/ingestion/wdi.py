from __future__ import annotations

import json
from urllib.parse import quote, urlencode
from urllib.request import urlopen

import pandas as pd


def build_wdi_indicator_url(
    api_base_url: str,
    indicator_id: str,
    *,
    country_selector: str,
    per_page: int,
    mrv: int | None = None,
) -> str:
    query = {"format": "json", "per_page": per_page}
    if mrv is not None:
        query["mrv"] = mrv
    encoded_country_selector = quote(country_selector, safe=";")
    return f"{api_base_url.rstrip('/')}/country/{encoded_country_selector}/indicator/{indicator_id}?{urlencode(query)}"


def fetch_wdi_indicator_payload(
    api_base_url: str,
    indicator_id: str,
    *,
    country_selector: str,
    per_page: int,
    mrv: int | None = None,
) -> str:
    url = build_wdi_indicator_url(
        api_base_url,
        indicator_id,
        country_selector=country_selector,
        per_page=per_page,
        mrv=mrv,
    )
    return urlopen(url, timeout=60).read().decode("utf-8")


def parse_wdi_indicator_payload(payload: str) -> tuple[dict[str, object], pd.DataFrame]:
    parsed = json.loads(payload)
    if not isinstance(parsed, list) or len(parsed) != 2:
        raise ValueError("Unexpected World Bank indicator payload structure.")
    metadata, rows = parsed
    return metadata, pd.DataFrame(rows)
