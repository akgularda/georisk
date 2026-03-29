from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.unctad import parse_unctad_snapshot_csv
from src.data_platform.normalization.unctad import normalize_unctad_snapshot


def test_parse_and_normalize_unctad_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "unctad_shipping_sample.csv").read_text(encoding="utf-8")

    parsed = parse_unctad_snapshot_csv(payload)
    normalized = normalize_unctad_snapshot(
        parsed,
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )

    assert not parsed.empty
    assert normalized["source_name"].eq("unctad").all()
    assert normalized["country_iso3"].eq("IRN").any()
    assert normalized["shipping_lsci_index"].max() == 60.3
    assert normalized["shipping_port_connectivity_index"].min() == 38.0
    assert normalized["publication_ts_utc"].notna().all()
