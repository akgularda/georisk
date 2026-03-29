from __future__ import annotations

from pathlib import Path

from src.data_platform.ingestion.unhcr import parse_unhcr_population_payload
from src.data_platform.normalization.unhcr import normalize_unhcr_origin_population


def test_parse_unhcr_population_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "unhcr_population_sample.json").read_text(encoding="utf-8")

    parsed = parse_unhcr_population_payload(payload)
    normalized = normalize_unhcr_origin_population(parsed)

    assert not parsed.empty
    assert "coo_iso" in parsed.columns
    assert "country_id" in normalized.columns
    assert normalized["country_id"].notna().any()

