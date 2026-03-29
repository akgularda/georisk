from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.idea import parse_idea_election_calendar_csv
from src.data_platform.normalization.idea import normalize_idea_election_calendar


def test_parse_and_normalize_idea_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "idea_elections_sample.csv").read_text(encoding="utf-8")

    parsed = parse_idea_election_calendar_csv(payload)
    normalized = normalize_idea_election_calendar(parsed, ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"))

    assert not parsed.empty
    assert "election_date" in parsed.columns
    assert set(normalized["country_iso3"]) == {"AFG", "IRN", "UKR"}
    assert {"source_record_id", "election_date", "publication_ts_utc", "ingestion_ts_utc"}.issubset(
        normalized.columns
    )
    iran = normalized.loc[normalized["country_iso3"] == "IRN"].sort_values("election_date").iloc[0]
    assert iran["election_date"] == pd.Timestamp("2026-03-01")
    assert iran["status"] == "held"
