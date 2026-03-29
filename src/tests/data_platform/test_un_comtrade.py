from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.un_comtrade import parse_un_comtrade_snapshot_csv
from src.data_platform.normalization.un_comtrade import normalize_un_comtrade_snapshot


def test_parse_and_normalize_un_comtrade_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "un_comtrade_sample.csv").read_text(encoding="utf-8")

    parsed = parse_un_comtrade_snapshot_csv(payload)
    normalized = normalize_un_comtrade_snapshot(
        parsed,
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )

    assert not parsed.empty
    assert normalized["source_name"].eq("un_comtrade").all()
    iran_latest = normalized.loc[
        (normalized["country_iso3"] == "IRN") & (normalized["observation_date"] == pd.Timestamp("2026-03-20"))
    ]
    assert not iran_latest.empty
    assert iran_latest["trade_exports_value_usd"].iloc[0] == 13500000000
    assert normalized["trade_exports_3m_change_pct"].min() == -2.1
    assert normalized["publication_ts_utc"].notna().all()
