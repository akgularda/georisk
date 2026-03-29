from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.acled import parse_acled_csv
from src.data_platform.normalization.acled import normalize_acled_events


def test_parse_and_normalize_acled_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "acled_sample.csv").read_text(encoding="utf-8")

    parsed = parse_acled_csv(payload)
    normalized = normalize_acled_events(parsed, ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"))

    assert not parsed.empty
    assert "event_id_cnty" in parsed.columns
    assert "source_record_id" in normalized.columns
    assert "country_iso3" in normalized.columns
    assert normalized["country_iso3"].eq("IRN").all()
    assert normalized["event_date"].notna().all()
    assert normalized["fatalities"].ge(0).all()
    assert set(normalized["event_type_slug"]) >= {
        "protests",
        "riots",
        "violence_against_civilians",
        "explosions_remote_violence",
        "strategic_developments",
    }
