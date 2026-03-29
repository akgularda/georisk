from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.wgi import parse_wgi_snapshot_csv
from src.data_platform.normalization.wgi import normalize_wgi_snapshot


def test_parse_and_normalize_wgi_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "wgi_sample.csv").read_text(encoding="utf-8")

    parsed = parse_wgi_snapshot_csv(payload)
    normalized = normalize_wgi_snapshot(parsed, ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"))

    assert not parsed.empty
    assert "country_iso3" in parsed.columns
    assert set(normalized["country_iso3"]) == {"AFG", "IRN", "UKR"}
    assert {"source_record_id", "governance_score", "publication_ts_utc", "ingestion_ts_utc"}.issubset(
        normalized.columns
    )
    iran = normalized.loc[normalized["country_iso3"] == "IRN"].iloc[-1]
    assert iran["year"] == 2024
    assert iran["governance_score"] < 0
