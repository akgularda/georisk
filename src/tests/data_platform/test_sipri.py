from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.sipri import parse_sipri_snapshot_csv
from src.data_platform.normalization.sipri import normalize_sipri_snapshot


def test_parse_and_normalize_sipri_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "sipri_security_sample.csv").read_text(encoding="utf-8")

    parsed = parse_sipri_snapshot_csv(payload)
    normalized = normalize_sipri_snapshot(
        parsed,
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )

    assert not parsed.empty
    assert normalized["source_name"].eq("sipri").all()
    assert normalized["security_military_expenditure_usd"].max() == 64_700_000_000
    assert normalized["security_military_expenditure_pct_gdp"].max() == 18.7
    assert normalized["year"].notna().all()
