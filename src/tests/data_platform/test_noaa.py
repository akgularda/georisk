from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.noaa import parse_noaa_snapshot_csv
from src.data_platform.normalization.noaa import normalize_noaa_snapshot


def test_parse_and_normalize_noaa_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "noaa_climate_sample.csv").read_text(encoding="utf-8")

    parsed = parse_noaa_snapshot_csv(payload)
    normalized = normalize_noaa_snapshot(
        parsed,
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )

    assert not parsed.empty
    assert normalized["source_name"].eq("noaa").all()
    assert normalized["climate_drought_severity_index"].max() == 4.6
    assert normalized["climate_temperature_anomaly_c"].min() == 1.1
    assert normalized["publication_ts_utc"].notna().all()
