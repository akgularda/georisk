from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd


def build_unhcr_population_url(base_url: str, *, year: int, page: int, limit: int) -> str:
    query = urlencode(
        {
            "year": year,
            "cf_type": "ISO",
            "page": page,
            "limit": limit,
            "coo_all": "true",
        }
    )
    return f"{base_url}?{query}"


def fetch_unhcr_population_page(base_url: str, *, year: int, page: int, limit: int) -> str:
    url = build_unhcr_population_url(base_url, year=year, page=page, limit=limit)
    return urlopen(url, timeout=60).read().decode("utf-8")


def parse_unhcr_population_payload(payload: str) -> pd.DataFrame:
    parsed = json.loads(payload)
    return pd.DataFrame(parsed.get("items", []))
