from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data_platform.ingestion.fao import parse_fao_snapshot_csv
from src.data_platform.ingestion.acled import parse_acled_csv
from src.data_platform.ingestion.imf import parse_imf_snapshot_csv
from src.data_platform.ingestion.idea import parse_idea_election_calendar_csv
from src.data_platform.ingestion.nasa_black_marble import parse_nasa_black_marble_snapshot_csv
from src.data_platform.ingestion.noaa import parse_noaa_snapshot_csv
from src.data_platform.ingestion.sipri import parse_sipri_snapshot_csv
from src.data_platform.ingestion.un_comtrade import parse_un_comtrade_snapshot_csv
from src.data_platform.ingestion.unctad import parse_unctad_snapshot_csv
from src.data_platform.ingestion.gdelt import parse_gdelt_export_lines, parse_gdelt_gkg_lines
from src.data_platform.ingestion.ucdp_onset import parse_ucdp_onset_csv
from src.data_platform.ingestion.ucdp import parse_ucdp_ged_csv
from src.data_platform.ingestion.unhcr import parse_unhcr_population_payload
from src.data_platform.ingestion.wdi import parse_wdi_indicator_payload
from src.data_platform.normalization.fao import normalize_fao_snapshot
from src.data_platform.normalization.acled import normalize_acled_events
from src.data_platform.normalization.imf import normalize_imf_snapshot
from src.data_platform.normalization.idea import normalize_idea_election_calendar
from src.data_platform.normalization.nasa_black_marble import normalize_nasa_black_marble_snapshot
from src.data_platform.normalization.noaa import normalize_noaa_snapshot
from src.data_platform.normalization.un_comtrade import normalize_un_comtrade_snapshot
from src.data_platform.normalization.unctad import normalize_unctad_snapshot
from src.data_platform.normalization.gdelt import normalize_gdelt_events, normalize_gdelt_gkg_documents
from src.data_platform.normalization.sipri import normalize_sipri_snapshot
from src.data_platform.normalization.ucdp_onset import normalize_ucdp_onset_dataset
from src.data_platform.normalization.ucdp import normalize_ucdp_ged_events
from src.data_platform.normalization.unhcr import normalize_unhcr_origin_population
from src.data_platform.normalization.wgi import normalize_wgi_snapshot
from src.data_platform.normalization.wdi import normalize_wdi_indicator_series, pivot_wdi_indicator_snapshot
from src.data_platform.serving.country_week_features import build_country_week_features


def _load_real_source_country_week_inputs() -> dict[str, pd.DataFrame]:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "real_source"

    gdelt_events = normalize_gdelt_events(
        parse_gdelt_export_lines((fixture_dir / "gdelt_export_sample.tsv").read_text(encoding="utf-8").splitlines())
    )
    gdelt_documents = normalize_gdelt_gkg_documents(
        parse_gdelt_gkg_lines((fixture_dir / "gdelt_gkg_sample.tsv").read_text(encoding="utf-8").splitlines())
    )
    acled_events = normalize_acled_events(
        parse_acled_csv((fixture_dir / "acled_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
    )
    imf = normalize_imf_snapshot(
        parse_imf_snapshot_csv((fixture_dir / "imf_commodity_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )
    fao = normalize_fao_snapshot(
        parse_fao_snapshot_csv((fixture_dir / "fao_food_price_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )
    wgi = normalize_wgi_snapshot(
        pd.read_csv(fixture_dir / "wgi_sample.csv"),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
    )
    idea = normalize_idea_election_calendar(
        parse_idea_election_calendar_csv((fixture_dir / "idea_elections_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
    )
    noaa = normalize_noaa_snapshot(
        parse_noaa_snapshot_csv((fixture_dir / "noaa_climate_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )
    sipri = normalize_sipri_snapshot(
        parse_sipri_snapshot_csv((fixture_dir / "sipri_security_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )
    nasa_black_marble = normalize_nasa_black_marble_snapshot(
        parse_nasa_black_marble_snapshot_csv((fixture_dir / "nasa_black_marble_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )
    un_comtrade = normalize_un_comtrade_snapshot(
        parse_un_comtrade_snapshot_csv((fixture_dir / "un_comtrade_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )
    unctad = normalize_unctad_snapshot(
        parse_unctad_snapshot_csv((fixture_dir / "unctad_shipping_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
        publication_ts_utc=pd.Timestamp("2026-03-20T00:00:00Z"),
    )
    ucdp_events = normalize_ucdp_ged_events(
        parse_ucdp_ged_csv((fixture_dir / "ucdp_ged_sample.csv").read_text(encoding="utf-8")),
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
    )
    ucdp_interstate_onset = normalize_ucdp_onset_dataset(
        parse_ucdp_onset_csv((fixture_dir / "ucdp_interstate_country_onset_251.csv").read_text(encoding="utf-8")),
        onset_type="interstate",
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
    )
    ucdp_intrastate_onset = normalize_ucdp_onset_dataset(
        parse_ucdp_onset_csv((fixture_dir / "ucdp_intrastate_country_onset_251.csv").read_text(encoding="utf-8")),
        onset_type="intrastate",
        ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"),
    )
    unhcr = normalize_unhcr_origin_population((parse_unhcr_population_payload((fixture_dir / "unhcr_population_sample.json").read_text(encoding="utf-8"))))

    wdi_frames: list[pd.DataFrame] = []
    for file_name in ["wdi_gdp_growth_sample.json", "wdi_inflation_sample.json", "wdi_population_sample.json"]:
        metadata, parsed = parse_wdi_indicator_payload((fixture_dir / file_name).read_text(encoding="utf-8"))
        wdi_frames.append(
            normalize_wdi_indicator_series(parsed, metadata, ingested_at=pd.Timestamp("2026-03-26T00:00:00Z"))
        )
    wdi_snapshot = pivot_wdi_indicator_snapshot(pd.concat(wdi_frames, ignore_index=True))

    return {
        "gdelt_events": gdelt_events,
        "gdelt_documents": gdelt_documents,
        "acled_events": acled_events,
        "imf_snapshot": imf,
        "fao_snapshot": fao,
        "wgi_snapshot": wgi,
        "idea_elections": idea,
        "noaa_snapshot": noaa,
        "sipri_snapshot": sipri,
        "nasa_black_marble_snapshot": nasa_black_marble,
        "un_comtrade_snapshot": un_comtrade,
        "unctad_snapshot": unctad,
        "ucdp_events": ucdp_events,
        "ucdp_interstate_onset": ucdp_interstate_onset,
        "ucdp_intrastate_onset": ucdp_intrastate_onset,
        "wdi_snapshot": wdi_snapshot,
        "unhcr_origin_population": unhcr,
    }


def test_build_country_week_features_from_real_source_snapshots() -> None:
    gold = build_country_week_features(
        **_load_real_source_country_week_inputs(),
        panel_start_date=pd.Timestamp("2026-02-16"),
        panel_end_date=pd.Timestamp("2026-03-23"),
        snapshot_ts_utc=pd.Timestamp("2026-03-26T00:00:00Z"),
    )

    expected_weeks = [
        pd.Timestamp("2026-02-16").date(),
        pd.Timestamp("2026-02-23").date(),
        pd.Timestamp("2026-03-02").date(),
        pd.Timestamp("2026-03-09").date(),
        pd.Timestamp("2026-03-16").date(),
        pd.Timestamp("2026-03-23").date(),
    ]

    colombia = gold.loc[gold["country_iso3"] == "COL"].reset_index(drop=True)
    assert colombia["week_start_date"].tolist() == expected_weeks
    assert set(colombia["acled_event_count_7d"].tolist()) == {0}
    assert colombia["macro_population_total"].notna().all()
    assert set(colombia["country_name"].tolist()) == {"Colombia"}

    afg_current_week = gold.loc[
        (gold["country_iso3"] == "AFG") & (gold["week_start_date"] == pd.Timestamp("2026-03-23").date())
    ]
    assert not afg_current_week.empty
    assert afg_current_week.iloc[0]["region_name"] == "Asia"

    iran_week = gold.loc[(gold["country_iso3"] == "IRN") & (gold["week_start_date"] == pd.Timestamp("2026-03-16").date())]
    assert not iran_week.empty
    iran_zero_week = iran_week.iloc[0]
    assert iran_zero_week["acled_event_count_7d"] == 0
    assert iran_zero_week["acled_riot_count_7d"] == 0
    assert iran_zero_week["trade_exports_value_usd"] == pytest.approx(12_000_000_000)
    assert iran_zero_week["shipping_lsci_index"] == pytest.approx(42.5)

    iran_known_label_week = gold.loc[
        (gold["country_iso3"] == "IRN") & (gold["week_start_date"] == pd.Timestamp("2026-02-16").date())
    ]
    assert not iran_known_label_week.empty
    assert not pd.isna(iran_known_label_week.iloc[0]["label_escalation_30d"])
    assert pd.isna(iran_known_label_week.iloc[0]["label_onset_30d"])
    assert pd.isna(iran_known_label_week.iloc[0]["label_onset_90d"])
    assert pd.isna(iran_known_label_week.iloc[0]["label_interstate_onset_30d"])
    assert pd.isna(iran_known_label_week.iloc[0]["label_interstate_onset_90d"])

    iran_latest_week = gold.loc[
        (gold["country_iso3"] == "IRN") & (gold["week_start_date"] == pd.Timestamp("2026-03-23").date())
    ]
    assert not iran_latest_week.empty
    assert pd.isna(iran_latest_week.iloc[0]["label_escalation_30d"])
    assert pd.isna(iran_latest_week.iloc[0]["label_onset_90d"])
    assert pd.isna(iran_latest_week.iloc[0]["label_interstate_onset_30d"])

    assert {"country_iso3", "country_name", "region_name", "week_start_date", "label_escalation_7d", "label_onset_90d", "label_interstate_onset_30d", "gdelt_event_count_7d", "macro_cpi_yoy"}.issubset(
        gold.columns
    )
    assert gold["label_interstate_30d"].equals(gold["label_interstate_onset_30d"])


def test_build_country_week_features_uses_latest_observation_up_to_week() -> None:
    gold = build_country_week_features(
        **_load_real_source_country_week_inputs(),
        panel_start_date=pd.Timestamp("2026-03-16"),
        panel_end_date=pd.Timestamp("2026-03-23"),
        snapshot_ts_utc=pd.Timestamp("2026-03-26T00:00:00Z"),
    )
    assert not gold.empty
    assert "AFG" in set(gold["country_iso3"])
    iran_week = gold.loc[(gold["country_iso3"] == "IRN") & (gold["week_start_date"] == pd.Timestamp("2026-03-23").date())]
    assert not iran_week.empty
    row = iran_week.iloc[0]
    assert row["acled_event_count_7d"] >= 1
    assert row["acled_event_count_28d"] > row["acled_event_count_7d"]
    assert row["acled_riot_count_7d"] >= 1
    assert row["acled_violence_against_civilians_count_7d"] >= 1
    assert row["market_oil_price_usd_per_barrel"] == 84.5
    assert row["market_gas_price_index"] == 112.0
    assert row["market_fertilizer_price_index"] == 152.0
    assert row["market_commodity_price_index"] == 126.0
    assert row["food_price_index"] == 104.7
    assert row["food_cereal_price_index"] == 99.1
    assert row["trade_exports_value_usd"] == pytest.approx(13_500_000_000)
    assert row["trade_imports_value_usd"] == pytest.approx(16_000_000_000)
    assert row["trade_exports_3m_change_pct"] == pytest.approx(4.0)
    assert row["trade_imports_3m_change_pct"] == pytest.approx(6.2)
    assert row["shipping_lsci_index"] == pytest.approx(44.1)
    assert row["shipping_port_connectivity_index"] == pytest.approx(39.6)
    assert row["governance_score"] < 0
    assert row["days_since_last_election"] == 22
    assert row["days_to_next_election"] == 20
    assert row["election_upcoming_30d"] == 1
    assert row["election_upcoming_90d"] == 1
    assert row["election_recent_30d"] == 1
    assert row["election_recent_90d"] == 1
    assert row["acled_distinct_actor1_count_7d"] >= 1
    assert row["acled_distinct_actor2_count_7d"] >= 1
    assert row["climate_drought_severity_index"] == pytest.approx(2.8)
    assert row["climate_temperature_anomaly_c"] == pytest.approx(1.7)
    assert row["climate_precipitation_anomaly_pct"] == pytest.approx(-18.0)
    assert row["climate_night_lights_anomaly_pct"] == pytest.approx(-3.4)
    assert row["climate_night_lights_zscore"] == pytest.approx(-0.6)
    assert row["security_military_expenditure_usd"] == pytest.approx(10_300_000_000)
    assert row["security_military_expenditure_pct_gdp"] == pytest.approx(2.4)
    assert row["security_arms_import_volume_index"] == pytest.approx(46.0)
    assert gold["snapshot_ts_utc"].notna().all()
    assert "ucdp_history_event_count_52w" in gold.columns
    assert gold["macro_population_total"].notna().any()
    assert "gdelt_event_count_28d" in gold.columns
    assert "gdelt_document_count_28d" in gold.columns
    assert "gdelt_event_count_7d_delta" in gold.columns
    assert "gdelt_document_count_7d_delta" in gold.columns
    assert "acled_event_count_7d_delta" in gold.columns
    assert "acled_fatalities_sum_7d_delta" in gold.columns
    assert "acled_protest_count_7d_delta" in gold.columns
    assert "acled_riot_count_7d_delta" in gold.columns
    assert "organized_violence_quiet_56d" in gold.columns
    assert row["gdelt_event_count_28d"] >= row["gdelt_event_count_7d"]
    assert row["gdelt_document_count_28d"] >= row["gdelt_document_count_7d"]
    assert row["gdelt_event_count_7d_delta"] == pytest.approx(row["gdelt_event_count_7d"] - (row["gdelt_event_count_28d"] / 4.0))
    assert row["gdelt_document_count_7d_delta"] == pytest.approx(
        row["gdelt_document_count_7d"] - (row["gdelt_document_count_28d"] / 4.0)
    )
    assert row["acled_event_count_7d_delta"] == pytest.approx(row["acled_event_count_7d"] - (row["acled_event_count_28d"] / 4.0))
    assert row["acled_fatalities_sum_7d_delta"] == pytest.approx(
        row["acled_fatalities_sum_7d"] - (row["acled_fatalities_sum_28d"] / 4.0)
    )
    assert row["organized_violence_quiet_56d"] in {0, 1}


def test_build_country_week_features_uses_official_onset_truth_for_conflict_and_interstate_labels() -> None:
    inputs = _load_real_source_country_week_inputs()
    inputs["ucdp_events"] = pd.DataFrame(
        [
            {
                "source_name": "ucdp_ged",
                "source_record_id": "onset-1",
                "country_iso3": "IRN",
                "country_name": "Iran",
                "region_name": "Asia",
                "admin1_name": pd.NA,
                "admin2_name": pd.NA,
                "event_date_start": pd.Timestamp("2024-01-19"),
                "event_date_end": pd.Timestamp("2024-01-19"),
                "publication_ts_utc": pd.Timestamp("2024-01-20T00:00:00Z"),
                "ingestion_ts_utc": pd.Timestamp("2026-03-29T00:00:00Z"),
                "event_type": "state_based",
                "type_of_violence": 1,
                "conflict_name": "Iran interstate crisis",
                "conflict_dset_id": 999,
                "conflict_new_id": 999,
                "side_a": "Iran",
                "side_b": "Other state",
                "best_fatalities": 3.0,
                "high_fatalities": 3.0,
                "low_fatalities": 3.0,
                "latitude": pd.NA,
                "longitude": pd.NA,
                "location_precision": pd.NA,
                "year": 2024,
            }
        ]
    )
    inputs["ucdp_interstate_onset"] = pd.DataFrame(
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
    inputs["ucdp_intrastate_onset"] = pd.DataFrame(columns=inputs["ucdp_interstate_onset"].columns)

    gold = build_country_week_features(
        **inputs,
        panel_start_date=pd.Timestamp("2024-01-01"),
        panel_end_date=pd.Timestamp("2024-01-29"),
        snapshot_ts_utc=pd.Timestamp("2024-12-31T00:00:00Z"),
    )

    pre_onset_week = gold.loc[
        (gold["country_iso3"] == "IRN") & (gold["week_start_date"] == pd.Timestamp("2024-01-01").date())
    ]
    assert not pre_onset_week.empty
    row = pre_onset_week.iloc[0]
    assert row["label_onset_30d"] == 1
    assert row["label_onset_90d"] == 1
    assert row["label_interstate_onset_30d"] == 1
    assert row["label_interstate_onset_90d"] == 1
    assert row["label_interstate_30d"] == 1
