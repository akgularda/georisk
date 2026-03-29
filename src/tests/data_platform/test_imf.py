from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.imf import parse_imf_snapshot_csv
from src.data_platform.normalization.imf import normalize_imf_snapshot


def test_parse_and_normalize_imf_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "imf_commodity_sample.csv").read_text(encoding="utf-8")

    parsed = parse_imf_snapshot_csv(payload)
    normalized = normalize_imf_snapshot(
        parsed,
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )

    assert not parsed.empty
    assert "observation_date" in normalized.columns
    assert normalized["source_name"].eq("imf").all()
    assert normalized["market_oil_price_usd_per_barrel"].max() == 84.5
    assert normalized["market_fertilizer_price_index"].min() == 145.0
    assert normalized["publication_ts_utc"].notna().all()
