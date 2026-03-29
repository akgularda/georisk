from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.ucdp_onset import parse_ucdp_onset_csv
from src.data_platform.ingestion.ucdp import parse_ucdp_ged_csv
from src.data_platform.normalization.ucdp_onset import normalize_ucdp_onset_dataset
from src.data_platform.normalization.ucdp import normalize_ucdp_ged_events
from src.data_platform.serving.ucdp_onset import localize_ucdp_country_onsets


def test_parse_and_normalize_ucdp_ged_snapshot() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    payload = (fixture_dir / "ucdp_ged_sample.csv").read_text(encoding="utf-8")

    parsed = parse_ucdp_ged_csv(payload)
    normalized = normalize_ucdp_ged_events(parsed, ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"))

    assert not parsed.empty
    assert "id" in parsed.columns
    assert "source_record_id" in normalized.columns
    assert "country_iso3" in normalized.columns
    assert normalized["country_iso3"].notna().all()
    assert normalized["event_date_start"].notna().all()
    assert normalized["best_fatalities"].ge(0).all()


def test_parse_ucdp_ged_csv_handles_mixed_object_columns_for_parquet_roundtrip(tmp_path: Path) -> None:
    payload = """id,country,date_start,date_end,source_date,type_of_violence,best,high,low,latitude,longitude,where_prec,year,gwnoa
1,Iran,2024-01-01,2024-01-01,2024-01-02,1,1,1,1,35.0,51.0,1,2024,630
2,Iran,2024-01-02,2024-01-02,2024-01-03,1,0,0,0,35.0,51.0,1,2024,unknown
"""

    parsed = parse_ucdp_ged_csv(payload)
    parquet_path = tmp_path / "ucdp_raw.parquet"
    parsed.to_parquet(parquet_path, index=False)

    assert str(parsed["gwnoa"].dtype) == "string"
    assert parquet_path.exists()


def test_parse_and_normalize_ucdp_onset_snapshots() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"
    interstate_payload = (fixture_dir / "ucdp_interstate_country_onset_251.csv").read_text(encoding="utf-8")
    intrastate_payload = (fixture_dir / "ucdp_intrastate_country_onset_251.csv").read_text(encoding="utf-8")

    interstate = normalize_ucdp_onset_dataset(
        parse_ucdp_onset_csv(interstate_payload),
        onset_type="interstate",
        ingested_at=pd.Timestamp("2026-03-29T00:00:00Z"),
    )
    intrastate = normalize_ucdp_onset_dataset(
        parse_ucdp_onset_csv(intrastate_payload),
        onset_type="intrastate",
        ingested_at=pd.Timestamp("2026-03-29T00:00:00Z"),
    )

    assert not interstate.empty
    assert not intrastate.empty
    assert set(interstate["onset_type"].unique()) == {"interstate"}
    assert set(intrastate["onset_type"].unique()) == {"intrastate"}
    assert interstate["country_iso3"].notna().all()
    assert intrastate["country_iso3"].notna().all()
    assert {"conflict_ids", "onset1", "onset20", "year_prev"}.issubset(interstate.columns)


def test_localize_ucdp_country_onsets_prefers_conflict_id_match() -> None:
    ucdp_events = pd.DataFrame(
        [
            {
                "country_iso3": "IRN",
                "country_name": "Iran",
                "region_name": "Asia",
                "event_date_start": pd.Timestamp("2024-01-19"),
                "event_date_end": pd.Timestamp("2024-01-19"),
                "best_fatalities": 3.0,
                "high_fatalities": 3.0,
                "low_fatalities": 3.0,
                "type_of_violence": 1,
                "conflict_new_id": 999,
                "conflict_dset_id": 999,
            },
            {
                "country_iso3": "IRN",
                "country_name": "Iran",
                "region_name": "Asia",
                "event_date_start": pd.Timestamp("2024-01-05"),
                "event_date_end": pd.Timestamp("2024-01-05"),
                "best_fatalities": 1.0,
                "high_fatalities": 1.0,
                "low_fatalities": 1.0,
                "type_of_violence": 1,
                "conflict_new_id": 111,
                "conflict_dset_id": 111,
            },
        ]
    )
    interstate_onsets = pd.DataFrame(
        [
            {
                "source_name": "ucdp_onset",
                "onset_type": "interstate",
                "country_iso3": "IRN",
                "country_name": "Iran",
                "year": 2024,
                "newconf": 1,
                "onset1": 1,
                "onset2": 1,
                "onset3": 1,
                "onset5": 0,
                "onset10": 0,
                "onset20": 0,
                "conflict_ids": "999",
                "year_prev": 2023,
                "ingestion_ts_utc": pd.Timestamp("2026-03-29T00:00:00Z"),
            }
        ]
    )
    intrastate_onsets = pd.DataFrame(columns=interstate_onsets.columns)

    localized = localize_ucdp_country_onsets(
        ucdp_events=ucdp_events,
        interstate_onsets=interstate_onsets,
        intrastate_onsets=intrastate_onsets,
    )

    assert len(localized) == 1
    row = localized.iloc[0]
    assert row["country_iso3"] == "IRN"
    assert row["onset_type"] == "interstate"
    assert row["onset_date"] == pd.Timestamp("2024-01-19")
    assert row["localization_method"] == "conflict_id_match"
