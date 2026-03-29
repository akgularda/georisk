from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.wdi import parse_wdi_indicator_payload
from src.data_platform.normalization.wdi import normalize_wdi_indicator_series


def test_parse_and_normalize_wdi_indicator_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "wdi_gdp_growth_sample.json").read_text(encoding="utf-8")

    metadata, parsed = parse_wdi_indicator_payload(payload)
    normalized = normalize_wdi_indicator_series(
        parsed,
        metadata,
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
    )

    assert metadata["lastupdated"] == "2026-02-24"
    assert not parsed.empty
    assert "countryiso3code" in parsed.columns
    assert set(normalized["country_iso3"]) == {"AFG", "COL", "SDN", "SYR", "UKR"}
    assert {"country_iso3", "indicator_id", "year", "publication_ts_utc", "ingestion_ts_utc"}.issubset(
        normalized.columns
    )

