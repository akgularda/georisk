from __future__ import annotations

from pathlib import Path

from src.data_platform.ingestion.gdelt import parse_gdelt_export_lines, parse_gdelt_gkg_lines, parse_gdelt_lastupdate
from src.data_platform.normalization.gdelt import normalize_gdelt_events, normalize_gdelt_gkg_documents


def test_parse_gdelt_lastupdate_from_real_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    metadata = parse_gdelt_lastupdate((fixture_dir / "gdelt_lastupdate.txt").read_text(encoding="utf-8"))

    assert metadata.export_url.endswith(".export.CSV.zip")
    assert metadata.gkg_url.endswith(".gkg.csv.zip")
    assert metadata.export_size_bytes > 0


def test_parse_and_normalize_gdelt_export_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    lines = (fixture_dir / "gdelt_export_sample.tsv").read_text(encoding="utf-8").splitlines()

    parsed = parse_gdelt_export_lines(lines)
    normalized = normalize_gdelt_events(parsed)

    assert not parsed.empty
    assert "global_event_id" in parsed.columns
    assert "country_id" in normalized.columns
    assert "event_date" in normalized.columns
    assert normalized["country_id"].notna().any()


def test_parse_and_normalize_gdelt_gkg_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    lines = (fixture_dir / "gdelt_gkg_sample.tsv").read_text(encoding="utf-8").splitlines()

    parsed = parse_gdelt_gkg_lines(lines)
    normalized = normalize_gdelt_gkg_documents(parsed)

    assert not parsed.empty
    assert "document_identifier" in parsed.columns
    assert "document_country_id" in normalized.columns
    assert normalized["document_country_id"].notna().any()

