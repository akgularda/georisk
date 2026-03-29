from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.nasa_black_marble import parse_nasa_black_marble_snapshot_csv
from src.data_platform.normalization.nasa_black_marble import normalize_nasa_black_marble_snapshot


def test_parse_and_normalize_nasa_black_marble_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "nasa_black_marble_sample.csv").read_text(encoding="utf-8")

    parsed = parse_nasa_black_marble_snapshot_csv(payload)
    normalized = normalize_nasa_black_marble_snapshot(
        parsed,
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )

    assert not parsed.empty
    assert normalized["source_name"].eq("nasa_black_marble").all()
    assert normalized["climate_night_lights_anomaly_pct"].min() == -11.2
    assert normalized["climate_night_lights_zscore"].max() == -0.3
    assert normalized["publication_ts_utc"].notna().all()
