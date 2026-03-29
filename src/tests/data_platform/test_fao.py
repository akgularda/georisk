from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.fao import parse_fao_snapshot_csv
from src.data_platform.normalization.fao import normalize_fao_snapshot


def test_parse_and_normalize_fao_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "fao_food_price_sample.csv").read_text(encoding="utf-8")

    parsed = parse_fao_snapshot_csv(payload)
    normalized = normalize_fao_snapshot(
        parsed,
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )

    assert not parsed.empty
    assert "observation_date" in normalized.columns
    assert normalized["source_name"].eq("fao").all()
    march_20 = normalized.loc[normalized["observation_date"] == pd.Timestamp("2026-03-20")]
    assert march_20["food_price_index"].iloc[0] == 104.7
    assert march_20["food_cereal_price_index"].iloc[0] == 99.1
    assert normalized["publication_ts_utc"].notna().all()
