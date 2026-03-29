from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from src.data_platform.ingestion.acled import load_acled_snapshot
from src.data_platform.ingestion.fao import load_fao_snapshot
from src.data_platform.ingestion.imf import load_imf_snapshot
from src.data_platform.ingestion.idea import load_idea_election_calendar
from src.data_platform.ingestion.nasa_black_marble import load_nasa_black_marble_snapshot
from src.data_platform.ingestion.noaa import load_noaa_snapshot
from src.data_platform.ingestion.sipri import load_sipri_snapshot
from src.data_platform.ingestion.un_comtrade import load_un_comtrade_snapshot
from src.data_platform.ingestion.unctad import load_unctad_snapshot
from src.data_platform.ingestion.gdelt import (
    fetch_text,
    fetch_zip_lines,
    load_snapshot_text,
    parse_gdelt_export_lines,
    parse_gdelt_gkg_lines,
    parse_gdelt_lastupdate,
    select_recent_file_urls,
)
from src.data_platform.ingestion.ucdp import fetch_ucdp_ged_zip, parse_ucdp_ged_csv, parse_ucdp_ged_zip
from src.data_platform.ingestion.ucdp_onset import fetch_ucdp_onset_csv, parse_ucdp_onset_csv
from src.data_platform.ingestion.unhcr import fetch_unhcr_population_page, parse_unhcr_population_payload
from src.data_platform.ingestion.wgi import load_wgi_snapshot
from src.data_platform.ingestion.wdi import build_wdi_indicator_url, fetch_wdi_indicator_payload, parse_wdi_indicator_payload
from src.data_platform.normalization.acled import normalize_acled_events
from src.data_platform.normalization.fao import normalize_fao_snapshot
from src.data_platform.normalization.imf import normalize_imf_snapshot
from src.data_platform.normalization.idea import normalize_idea_election_calendar
from src.data_platform.normalization.nasa_black_marble import normalize_nasa_black_marble_snapshot
from src.data_platform.normalization.noaa import normalize_noaa_snapshot
from src.data_platform.normalization.gdelt import normalize_gdelt_events, normalize_gdelt_gkg_documents
from src.data_platform.normalization.sipri import normalize_sipri_snapshot
from src.data_platform.normalization.un_comtrade import normalize_un_comtrade_snapshot
from src.data_platform.normalization.unctad import normalize_unctad_snapshot
from src.data_platform.normalization.ucdp import normalize_ucdp_ged_events
from src.data_platform.normalization.ucdp_onset import normalize_ucdp_onset_dataset
from src.data_platform.normalization.unhcr import normalize_unhcr_origin_population
from src.data_platform.normalization.wgi import normalize_wgi_snapshot
from src.data_platform.normalization.wdi import normalize_wdi_indicator_series, pivot_wdi_indicator_snapshot
from src.data_platform.schemas import (
    CountryWeekFeaturesConfig,
    CountryWeekPipelineRunResult,
    LiveCountrySignalsConfig,
    PipelineRunResult,
)
from src.data_platform.serving.country_week_features import build_country_week_features
from src.data_platform.serving.entity_day_features import build_gold_entity_day_features
from src.data_platform.serving.entity_day_labels import build_gold_entity_day_labels
from src.data_platform.serving.live_signals import build_gold_country_live_signals
from src.data_platform.serving.report_inputs import build_gold_report_inputs
from src.data_platform.serving.social_inputs import build_gold_social_inputs
from src.data_platform.storage import ensure_layer_dir
from src.data_platform.validation.reports import summarize_table
from src.forecasting.utils import load_yaml_config, project_root, resolve_path, write_json


def _load_snapshot_dir() -> Path:
    return project_root() / "src" / "tests" / "fixtures" / "real_source"


def _resolve_storage_root(storage_root: Path, output_root: Path | None) -> Path:
    if output_root is not None:
        return (output_root / storage_root).resolve()
    return (project_root() / storage_root).resolve()


def _ensure_utc_timestamp(value: pd.Timestamp) -> pd.Timestamp:
    if value.tzinfo is None:
        return value.tz_localize("UTC")
    return value.tz_convert("UTC")


def _write_validation_report(output_dir: Path, table_name: str, frame: pd.DataFrame, *, key_columns: list[str]) -> Path:
    validation_report_file = output_dir / "validation_report.json"
    write_json(
        validation_report_file,
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tables": [summarize_table(table_name, frame, key_columns=key_columns)],
        },
    )
    return validation_report_file


def _validation_entry(table_name: str, frame: pd.DataFrame, *, key_columns: list[str]) -> dict[str, object]:
    return summarize_table(table_name, frame, key_columns=key_columns)


def _fetch_gdelt_frames(config: LiveCountrySignalsConfig, *, use_test_snapshots: bool) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    raw_manifest: dict[str, object] = {"source": "gdelt"}
    if use_test_snapshots:
        snapshot_dir = _load_snapshot_dir()
        lastupdate_text = load_snapshot_text(snapshot_dir / "gdelt_lastupdate.txt")
        export_lines = (snapshot_dir / "gdelt_export_sample.tsv").read_text(encoding="utf-8").splitlines()
        gkg_lines = (snapshot_dir / "gdelt_gkg_sample.tsv").read_text(encoding="utf-8").splitlines()
        raw_manifest["mode"] = "snapshot"
        raw_manifest["snapshot_dir"] = str(snapshot_dir)
    else:
        lastupdate_text = fetch_text(config.gdelt.lastupdate_url)
        masterfile_text = fetch_text(config.gdelt.masterfile_url)
        export_urls = select_recent_file_urls(masterfile_text, ".export.CSV.zip", config.gdelt.export_file_limit)
        gkg_urls = select_recent_file_urls(masterfile_text, ".gkg.csv.zip", config.gdelt.gkg_file_limit)
        export_lines = []
        for url in export_urls:
            export_lines.extend(fetch_zip_lines(url))
        gkg_lines = []
        for url in gkg_urls:
            gkg_lines.extend(fetch_zip_lines(url))
        raw_manifest["mode"] = "live"
        raw_manifest["export_urls"] = export_urls
        raw_manifest["gkg_urls"] = gkg_urls

    lastupdate = parse_gdelt_lastupdate(lastupdate_text)
    raw_manifest["lastupdate"] = lastupdate.__dict__
    return parse_gdelt_export_lines(export_lines), parse_gdelt_gkg_lines(gkg_lines), raw_manifest


def _fetch_unhcr_frame(config: LiveCountrySignalsConfig, *, use_test_snapshots: bool) -> tuple[pd.DataFrame, dict[str, object]]:
    raw_manifest: dict[str, object] = {"source": "unhcr"}
    if use_test_snapshots:
        snapshot_dir = _load_snapshot_dir()
        payload = (snapshot_dir / "unhcr_population_sample.json").read_text(encoding="utf-8")
        raw_manifest["mode"] = "snapshot"
        raw_manifest["snapshot_file"] = str(snapshot_dir / "unhcr_population_sample.json")
    else:
        frames: list[pd.DataFrame] = []
        page = 1
        while True:
            payload = fetch_unhcr_population_page(
                config.unhcr.population_base_url,
                year=config.unhcr.population_origin_year,
                page=page,
                limit=config.unhcr.page_size,
            )
            page_frame = parse_unhcr_population_payload(payload)
            if page_frame.empty:
                break
            frames.append(page_frame)
            if len(page_frame) < config.unhcr.page_size:
                break
            page += 1
        frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        raw_manifest["mode"] = "live"
        raw_manifest["pages_fetched"] = page
        return frame, raw_manifest
    return parse_unhcr_population_payload(payload), raw_manifest


def _flatten_wdi_bronze_frame(frame: pd.DataFrame, indicator_id: str) -> pd.DataFrame:
    bronze = frame.copy()
    bronze["requested_indicator_id"] = indicator_id
    bronze["country_api_id"] = bronze["country"].map(lambda raw: raw.get("id") if isinstance(raw, dict) else None)
    bronze["country_name"] = bronze["country"].map(lambda raw: raw.get("value") if isinstance(raw, dict) else None)
    bronze["indicator_api_id"] = bronze["indicator"].map(lambda raw: raw.get("id") if isinstance(raw, dict) else None)
    bronze["indicator_name"] = bronze["indicator"].map(lambda raw: raw.get("value") if isinstance(raw, dict) else None)
    return bronze.drop(columns=["country", "indicator"])


def _prepare_bronze_unhcr_frame(frame: pd.DataFrame) -> pd.DataFrame:
    bronze = frame.copy()
    return bronze.map(lambda value: None if pd.isna(value) else str(value))


def _fetch_wdi_frames(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[list[tuple[str, dict[str, object], pd.DataFrame]], dict[str, object]]:
    snapshot_files = {
        "NY.GDP.MKTP.KD.ZG": "wdi_gdp_growth_sample.json",
        "FP.CPI.TOTL.ZG": "wdi_inflation_sample.json",
        "SP.POP.TOTL": "wdi_population_sample.json",
    }
    raw_manifest: dict[str, object] = {"source": "world_bank_wdi", "indicators": {}}
    frames: list[tuple[str, dict[str, object], pd.DataFrame]] = []
    snapshot_dir = _load_snapshot_dir()
    for indicator_id in config.wdi.indicators.values():
        if use_test_snapshots:
            snapshot_file = snapshot_dir / snapshot_files[indicator_id]
            payload = snapshot_file.read_text(encoding="utf-8")
            metadata, frame = parse_wdi_indicator_payload(payload)
            raw_manifest["indicators"][indicator_id] = {
                "mode": "snapshot",
                "snapshot_file": str(snapshot_file),
                "lastupdated": metadata.get("lastupdated"),
            }
        else:
            payload = fetch_wdi_indicator_payload(
                config.wdi.api_base_url,
                indicator_id,
                country_selector=config.wdi.country_selector,
                per_page=config.wdi.per_page,
                mrv=config.wdi.mrv,
            )
            metadata, frame = parse_wdi_indicator_payload(payload)
            raw_manifest["indicators"][indicator_id] = {
                "mode": "live",
                "url": build_wdi_indicator_url(
                    config.wdi.api_base_url,
                    indicator_id,
                    country_selector=config.wdi.country_selector,
                    per_page=config.wdi.per_page,
                    mrv=config.wdi.mrv,
                ),
                "lastupdated": metadata.get("lastupdated"),
            }
        frames.append((indicator_id, metadata, frame))
    return frames, raw_manifest


def _fetch_ucdp_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    raw_manifest: dict[str, object] = {"source": "ucdp_ged"}
    if use_test_snapshots:
        snapshot_file = _load_snapshot_dir() / "ucdp_ged_sample.csv"
        raw_manifest["mode"] = "snapshot"
        raw_manifest["snapshot_file"] = str(snapshot_file)
        return parse_ucdp_ged_csv(snapshot_file.read_text(encoding="utf-8")), raw_manifest

    payload = fetch_ucdp_ged_zip(config.ucdp.download_url)
    raw_manifest["mode"] = "live"
    raw_manifest["download_url"] = config.ucdp.download_url
    return parse_ucdp_ged_zip(payload), raw_manifest


def _fetch_ucdp_onset_frames(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    raw_manifest: dict[str, object] = {"source": "ucdp_onset"}
    if use_test_snapshots:
        snapshot_dir = _load_snapshot_dir()
        interstate_file = snapshot_dir / "ucdp_interstate_country_onset_251.csv"
        intrastate_file = snapshot_dir / "ucdp_intrastate_country_onset_251.csv"
        raw_manifest["mode"] = "snapshot"
        raw_manifest["interstate_snapshot_file"] = str(interstate_file)
        raw_manifest["intrastate_snapshot_file"] = str(intrastate_file)
        return (
            parse_ucdp_onset_csv(interstate_file.read_text(encoding="utf-8")),
            parse_ucdp_onset_csv(intrastate_file.read_text(encoding="utf-8")),
            raw_manifest,
        )

    interstate_payload = fetch_ucdp_onset_csv(config.ucdp_onset.interstate_download_url)
    intrastate_payload = fetch_ucdp_onset_csv(config.ucdp_onset.intrastate_download_url)
    raw_manifest["mode"] = "live"
    raw_manifest["interstate_download_url"] = config.ucdp_onset.interstate_download_url
    raw_manifest["intrastate_download_url"] = config.ucdp_onset.intrastate_download_url
    return parse_ucdp_onset_csv(interstate_payload), parse_ucdp_onset_csv(intrastate_payload), raw_manifest


def _fetch_acled_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.acled.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "acled",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_acled_snapshot(snapshot_path), raw_manifest


def _fetch_imf_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.imf.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "imf",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_imf_snapshot(snapshot_path), raw_manifest


def _fetch_fao_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.fao.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "fao",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_fao_snapshot(snapshot_path), raw_manifest


def _fetch_wgi_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.wgi.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "wgi",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_wgi_snapshot(snapshot_path), raw_manifest


def _fetch_idea_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.idea.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "idea",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_idea_election_calendar(snapshot_path), raw_manifest


def _fetch_noaa_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.noaa.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "noaa",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_noaa_snapshot(snapshot_path), raw_manifest


def _fetch_sipri_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.sipri.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "sipri",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_sipri_snapshot(snapshot_path), raw_manifest


def _fetch_nasa_black_marble_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.nasa_black_marble.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "nasa_black_marble",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_nasa_black_marble_snapshot(snapshot_path), raw_manifest


def _fetch_un_comtrade_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.un_comtrade.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "un_comtrade",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_un_comtrade_snapshot(snapshot_path), raw_manifest


def _fetch_unctad_frame(
    config: CountryWeekFeaturesConfig,
    *,
    use_test_snapshots: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    snapshot_path = resolve_path(config.unctad.snapshot_file)
    raw_manifest: dict[str, object] = {
        "source": "unctad",
        "mode": "snapshot",
        "snapshot_file": str(snapshot_path),
    }
    return load_unctad_snapshot(snapshot_path), raw_manifest


def run_live_country_signals_pipeline(
    config_path: Path,
    *,
    output_root: Path | None = None,
    use_test_snapshots: bool = False,
) -> PipelineRunResult:
    config = load_yaml_config(config_path, LiveCountrySignalsConfig)
    storage_root = _resolve_storage_root(config.storage.storage_root, output_root)

    gdelt_export_raw, gdelt_gkg_raw, gdelt_manifest = _fetch_gdelt_frames(config, use_test_snapshots=use_test_snapshots)
    unhcr_raw, unhcr_manifest = _fetch_unhcr_frame(config, use_test_snapshots=use_test_snapshots)

    bronze_gdelt_dir = ensure_layer_dir(storage_root, "bronze", "gdelt")
    silver_gdelt_dir = ensure_layer_dir(storage_root, "silver", "gdelt")
    silver_unhcr_dir = ensure_layer_dir(storage_root, "silver", "unhcr")
    gold_dir = ensure_layer_dir(storage_root, "gold", "live_country_signals")
    raw_dir = ensure_layer_dir(storage_root, "raw", config.run_name)

    gdelt_export_raw.to_parquet(bronze_gdelt_dir / "gdelt_export.parquet", index=False)
    gdelt_gkg_raw.to_parquet(bronze_gdelt_dir / "gdelt_gkg.parquet", index=False)

    normalized_events = normalize_gdelt_events(gdelt_export_raw)
    normalized_documents = normalize_gdelt_gkg_documents(gdelt_gkg_raw)
    normalized_unhcr = normalize_unhcr_origin_population(unhcr_raw)

    normalized_events.to_parquet(silver_gdelt_dir / "events.parquet", index=False)
    normalized_documents.to_parquet(silver_gdelt_dir / "gkg_documents.parquet", index=False)
    normalized_unhcr.to_parquet(silver_unhcr_dir / "origin_population.parquet", index=False)

    gold_country_signals = build_gold_country_live_signals(normalized_events, normalized_documents, normalized_unhcr)
    gold_country_signals_file = gold_dir / "gold_country_live_signals.parquet"
    gold_country_signals.to_parquet(gold_country_signals_file, index=False)

    raw_manifest_file = raw_dir / "raw_manifest.json"
    write_json(raw_manifest_file, {"gdelt": gdelt_manifest, "unhcr": unhcr_manifest})

    validation_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tables": [
            summarize_table("silver_gdelt_events", normalized_events, key_columns=["country_id", "event_date"]),
            summarize_table("silver_gdelt_gkg_documents", normalized_documents, key_columns=["document_country_id", "document_date"]),
            summarize_table("silver_unhcr_origin_population", normalized_unhcr, key_columns=["country_id", "year"]),
            summarize_table("gold_country_live_signals", gold_country_signals, key_columns=["country_id", "as_of_date"]),
        ],
    }
    validation_report_file = gold_dir / "validation_report.json"
    write_json(validation_report_file, validation_report)

    return PipelineRunResult(
        raw_manifest_file=raw_manifest_file,
        validation_report_file=validation_report_file,
        gold_country_signals_file=gold_country_signals_file,
    )


def run_country_week_features_pipeline(
    config_path: Path,
    *,
    output_root: Path | None = None,
    use_test_snapshots: bool = False,
) -> CountryWeekPipelineRunResult:
    config = load_yaml_config(config_path, CountryWeekFeaturesConfig)
    storage_root = _resolve_storage_root(config.storage.storage_root, output_root)
    ingested_at = _ensure_utc_timestamp(pd.Timestamp(datetime.now(timezone.utc)))

    gdelt_export_raw, gdelt_gkg_raw, gdelt_manifest = _fetch_gdelt_frames(config, use_test_snapshots=use_test_snapshots)
    acled_raw, acled_manifest = _fetch_acled_frame(config, use_test_snapshots=use_test_snapshots)
    imf_raw, imf_manifest = _fetch_imf_frame(config, use_test_snapshots=use_test_snapshots)
    fao_raw, fao_manifest = _fetch_fao_frame(config, use_test_snapshots=use_test_snapshots)
    wgi_raw, wgi_manifest = _fetch_wgi_frame(config, use_test_snapshots=use_test_snapshots)
    idea_raw, idea_manifest = _fetch_idea_frame(config, use_test_snapshots=use_test_snapshots)
    noaa_raw, noaa_manifest = _fetch_noaa_frame(config, use_test_snapshots=use_test_snapshots)
    sipri_raw, sipri_manifest = _fetch_sipri_frame(config, use_test_snapshots=use_test_snapshots)
    nasa_black_marble_raw, nasa_black_marble_manifest = _fetch_nasa_black_marble_frame(
        config,
        use_test_snapshots=use_test_snapshots,
    )
    un_comtrade_raw, un_comtrade_manifest = _fetch_un_comtrade_frame(config, use_test_snapshots=use_test_snapshots)
    unctad_raw, unctad_manifest = _fetch_unctad_frame(config, use_test_snapshots=use_test_snapshots)
    unhcr_raw, unhcr_manifest = _fetch_unhcr_frame(config, use_test_snapshots=use_test_snapshots)
    ucdp_raw, ucdp_manifest = _fetch_ucdp_frame(config, use_test_snapshots=use_test_snapshots)
    ucdp_interstate_onset_raw, ucdp_intrastate_onset_raw, ucdp_onset_manifest = _fetch_ucdp_onset_frames(
        config,
        use_test_snapshots=use_test_snapshots,
    )
    wdi_raw_frames, wdi_manifest = _fetch_wdi_frames(config, use_test_snapshots=use_test_snapshots)

    bronze_gdelt_dir = ensure_layer_dir(storage_root, "bronze", "gdelt")
    bronze_acled_dir = ensure_layer_dir(storage_root, "bronze", "acled")
    bronze_imf_dir = ensure_layer_dir(storage_root, "bronze", "imf")
    bronze_fao_dir = ensure_layer_dir(storage_root, "bronze", "fao")
    bronze_wgi_dir = ensure_layer_dir(storage_root, "bronze", "wgi")
    bronze_idea_dir = ensure_layer_dir(storage_root, "bronze", "idea")
    bronze_noaa_dir = ensure_layer_dir(storage_root, "bronze", "noaa")
    bronze_sipri_dir = ensure_layer_dir(storage_root, "bronze", "sipri")
    bronze_nasa_black_marble_dir = ensure_layer_dir(storage_root, "bronze", "nasa_black_marble")
    bronze_un_comtrade_dir = ensure_layer_dir(storage_root, "bronze", "un_comtrade")
    bronze_unctad_dir = ensure_layer_dir(storage_root, "bronze", "unctad")
    bronze_unhcr_dir = ensure_layer_dir(storage_root, "bronze", "unhcr")
    bronze_ucdp_dir = ensure_layer_dir(storage_root, "bronze", "ucdp")
    bronze_ucdp_onset_dir = ensure_layer_dir(storage_root, "bronze", "ucdp_onset")
    bronze_wdi_dir = ensure_layer_dir(storage_root, "bronze", "wdi")
    silver_gdelt_dir = ensure_layer_dir(storage_root, "silver", "gdelt")
    silver_acled_dir = ensure_layer_dir(storage_root, "silver", "acled")
    silver_imf_dir = ensure_layer_dir(storage_root, "silver", "imf")
    silver_fao_dir = ensure_layer_dir(storage_root, "silver", "fao")
    silver_wgi_dir = ensure_layer_dir(storage_root, "silver", "wgi")
    silver_idea_dir = ensure_layer_dir(storage_root, "silver", "idea")
    silver_noaa_dir = ensure_layer_dir(storage_root, "silver", "noaa")
    silver_sipri_dir = ensure_layer_dir(storage_root, "silver", "sipri")
    silver_nasa_black_marble_dir = ensure_layer_dir(storage_root, "silver", "nasa_black_marble")
    silver_un_comtrade_dir = ensure_layer_dir(storage_root, "silver", "un_comtrade")
    silver_unctad_dir = ensure_layer_dir(storage_root, "silver", "unctad")
    silver_unhcr_dir = ensure_layer_dir(storage_root, "silver", "unhcr")
    silver_ucdp_dir = ensure_layer_dir(storage_root, "silver", "ucdp")
    silver_ucdp_onset_dir = ensure_layer_dir(storage_root, "silver", "ucdp_onset")
    silver_wdi_dir = ensure_layer_dir(storage_root, "silver", "wdi")
    gold_dir = ensure_layer_dir(storage_root, "gold", "country_week_features")
    entity_day_features_dir = ensure_layer_dir(storage_root, "gold", "entity_day_features")
    entity_day_labels_dir = ensure_layer_dir(storage_root, "gold", "entity_day_labels")
    report_inputs_dir = ensure_layer_dir(storage_root, "gold", "report_inputs")
    social_inputs_dir = ensure_layer_dir(storage_root, "gold", "social_inputs")
    raw_dir = ensure_layer_dir(storage_root, "raw", config.run_name)

    gdelt_export_raw.to_parquet(bronze_gdelt_dir / "gdelt_export.parquet", index=False)
    gdelt_gkg_raw.to_parquet(bronze_gdelt_dir / "gdelt_gkg.parquet", index=False)
    acled_raw.to_parquet(bronze_acled_dir / "events.parquet", index=False)
    imf_raw.to_parquet(bronze_imf_dir / "commodity_series.parquet", index=False)
    fao_raw.to_parquet(bronze_fao_dir / "food_price_series.parquet", index=False)
    wgi_raw.to_parquet(bronze_wgi_dir / "country_year_snapshot.parquet", index=False)
    idea_raw.to_parquet(bronze_idea_dir / "elections.parquet", index=False)
    noaa_raw.to_parquet(bronze_noaa_dir / "climate_series.parquet", index=False)
    sipri_raw.to_parquet(bronze_sipri_dir / "security_series.parquet", index=False)
    nasa_black_marble_raw.to_parquet(bronze_nasa_black_marble_dir / "night_lights_series.parquet", index=False)
    _prepare_bronze_unhcr_frame(unhcr_raw).to_parquet(bronze_unhcr_dir / "population.parquet", index=False)
    ucdp_raw.to_parquet(bronze_ucdp_dir / "ged.parquet", index=False)
    ucdp_interstate_onset_raw.to_parquet(bronze_ucdp_onset_dir / "interstate_country_onset.parquet", index=False)
    ucdp_intrastate_onset_raw.to_parquet(bronze_ucdp_onset_dir / "intrastate_country_onset.parquet", index=False)
    bronze_wdi = pd.concat(
        [_flatten_wdi_bronze_frame(frame, indicator_id) for indicator_id, _, frame in wdi_raw_frames],
        ignore_index=True,
    )
    bronze_wdi.to_parquet(bronze_wdi_dir / "indicator_series.parquet", index=False)

    normalized_events = normalize_gdelt_events(gdelt_export_raw)
    normalized_documents = normalize_gdelt_gkg_documents(gdelt_gkg_raw)
    normalized_acled = normalize_acled_events(acled_raw, ingested_at=ingested_at)
    normalized_imf = normalize_imf_snapshot(imf_raw, ingested_at=ingested_at, publication_ts_utc=config.imf.publication_ts_utc)
    normalized_fao = normalize_fao_snapshot(fao_raw, ingested_at=ingested_at, publication_ts_utc=config.fao.publication_ts_utc)
    normalized_wgi = normalize_wgi_snapshot(wgi_raw, ingested_at=ingested_at)
    normalized_idea = normalize_idea_election_calendar(idea_raw, ingested_at=ingested_at)
    normalized_noaa = normalize_noaa_snapshot(noaa_raw, ingested_at=ingested_at, publication_ts_utc=config.noaa.publication_ts_utc)
    normalized_sipri = normalize_sipri_snapshot(
        sipri_raw,
        ingested_at=ingested_at,
        publication_ts_utc=config.sipri.publication_ts_utc,
    )
    normalized_nasa_black_marble = normalize_nasa_black_marble_snapshot(
        nasa_black_marble_raw,
        ingested_at=ingested_at,
        publication_ts_utc=config.nasa_black_marble.publication_ts_utc,
    )
    normalized_un_comtrade = normalize_un_comtrade_snapshot(
        un_comtrade_raw,
        ingested_at=ingested_at,
        publication_ts_utc=config.un_comtrade.publication_ts_utc,
    )
    normalized_unctad = normalize_unctad_snapshot(
        unctad_raw,
        ingested_at=ingested_at,
        publication_ts_utc=config.unctad.publication_ts_utc,
    )
    normalized_unhcr = normalize_unhcr_origin_population(unhcr_raw)
    filtered_ucdp_raw = ucdp_raw.loc[pd.to_numeric(ucdp_raw["year"], errors="coerce") >= config.ucdp.min_year].copy()
    normalized_ucdp = normalize_ucdp_ged_events(filtered_ucdp_raw, ingested_at=ingested_at)
    normalized_ucdp_interstate_onset = normalize_ucdp_onset_dataset(
        ucdp_interstate_onset_raw,
        onset_type="interstate",
        ingested_at=ingested_at,
    )
    normalized_ucdp_intrastate_onset = normalize_ucdp_onset_dataset(
        ucdp_intrastate_onset_raw,
        onset_type="intrastate",
        ingested_at=ingested_at,
    )
    normalized_wdi = pd.concat(
        [
            normalize_wdi_indicator_series(frame, metadata, ingested_at=ingested_at)
            for _, metadata, frame in wdi_raw_frames
        ],
        ignore_index=True,
    )
    wdi_snapshot = pivot_wdi_indicator_snapshot(normalized_wdi)

    normalized_events.to_parquet(silver_gdelt_dir / "events.parquet", index=False)
    normalized_documents.to_parquet(silver_gdelt_dir / "gkg_documents.parquet", index=False)
    normalized_acled.to_parquet(silver_acled_dir / "events.parquet", index=False)
    normalized_imf.to_parquet(silver_imf_dir / "commodity_series.parquet", index=False)
    normalized_fao.to_parquet(silver_fao_dir / "food_price_series.parquet", index=False)
    normalized_wgi.to_parquet(silver_wgi_dir / "country_year_snapshot.parquet", index=False)
    normalized_idea.to_parquet(silver_idea_dir / "elections.parquet", index=False)
    normalized_noaa.to_parquet(silver_noaa_dir / "climate_series.parquet", index=False)
    normalized_sipri.to_parquet(silver_sipri_dir / "security_series.parquet", index=False)
    normalized_nasa_black_marble.to_parquet(silver_nasa_black_marble_dir / "night_lights_series.parquet", index=False)
    normalized_un_comtrade.to_parquet(silver_un_comtrade_dir / "trade_series.parquet", index=False)
    normalized_unctad.to_parquet(silver_unctad_dir / "shipping_series.parquet", index=False)
    normalized_unhcr.to_parquet(silver_unhcr_dir / "origin_population.parquet", index=False)
    normalized_ucdp.to_parquet(silver_ucdp_dir / "events.parquet", index=False)
    normalized_ucdp_interstate_onset.to_parquet(silver_ucdp_onset_dir / "interstate_country_onset.parquet", index=False)
    normalized_ucdp_intrastate_onset.to_parquet(silver_ucdp_onset_dir / "intrastate_country_onset.parquet", index=False)
    normalized_wdi.to_parquet(silver_wdi_dir / "indicator_series.parquet", index=False)
    wdi_snapshot.to_parquet(silver_wdi_dir / "country_year_snapshot.parquet", index=False)

    gold_country_week_features = build_country_week_features(
        gdelt_events=normalized_events,
        gdelt_documents=normalized_documents,
        acled_events=normalized_acled,
        imf_snapshot=normalized_imf,
        fao_snapshot=normalized_fao,
        wgi_snapshot=normalized_wgi,
        idea_elections=normalized_idea,
        noaa_snapshot=normalized_noaa,
        sipri_snapshot=normalized_sipri,
        nasa_black_marble_snapshot=normalized_nasa_black_marble,
        un_comtrade_snapshot=normalized_un_comtrade,
        unctad_snapshot=normalized_unctad,
        ucdp_events=normalized_ucdp,
        ucdp_interstate_onset=normalized_ucdp_interstate_onset,
        ucdp_intrastate_onset=normalized_ucdp_intrastate_onset,
        wdi_snapshot=wdi_snapshot,
        unhcr_origin_population=normalized_unhcr,
        panel_start_date=config.panel.start_date,
        panel_end_date=config.panel.end_date,
        snapshot_ts_utc=ingested_at,
    )
    gold_country_week_features_file = gold_dir / "country_week_features.parquet"
    gold_country_week_features.to_parquet(gold_country_week_features_file, index=False)

    gold_entity_day_features = build_gold_entity_day_features(gold_country_week_features)
    gold_entity_day_features_file = entity_day_features_dir / "entity_day_features.parquet"
    gold_entity_day_features.to_parquet(gold_entity_day_features_file, index=False)

    gold_entity_day_labels = build_gold_entity_day_labels(gold_country_week_features)
    gold_entity_day_labels_file = entity_day_labels_dir / "entity_day_labels.parquet"
    gold_entity_day_labels.to_parquet(gold_entity_day_labels_file, index=False)

    gold_report_inputs = build_gold_report_inputs(gold_country_week_features)
    gold_report_inputs_file = report_inputs_dir / "report_inputs.parquet"
    gold_report_inputs.to_parquet(gold_report_inputs_file, index=False)

    gold_social_inputs = build_gold_social_inputs(gold_country_week_features)
    gold_social_inputs_file = social_inputs_dir / "social_inputs.parquet"
    gold_social_inputs.to_parquet(gold_social_inputs_file, index=False)

    raw_manifest_file = raw_dir / "raw_manifest.json"
    write_json(
        raw_manifest_file,
        {
            "gdelt": gdelt_manifest,
            "acled": acled_manifest,
            "imf": imf_manifest,
            "fao": fao_manifest,
            "wgi": wgi_manifest,
            "idea": idea_manifest,
            "noaa": noaa_manifest,
            "sipri": sipri_manifest,
            "nasa_black_marble": nasa_black_marble_manifest,
            "un_comtrade": un_comtrade_manifest,
            "unctad": unctad_manifest,
            "unhcr": unhcr_manifest,
            "ucdp": ucdp_manifest,
            "ucdp_onset": ucdp_onset_manifest,
            "wdi": wdi_manifest,
        },
    )

    validation_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tables": [
            _validation_entry("silver_gdelt_events", normalized_events, key_columns=["country_id", "event_date"]),
            _validation_entry("silver_gdelt_gkg_documents", normalized_documents, key_columns=["document_country_id", "document_date"]),
            _validation_entry("silver_acled_events", normalized_acled, key_columns=["country_iso3", "event_date", "source_record_id"]),
            _validation_entry("silver_imf_commodity_series", normalized_imf, key_columns=["observation_date"]),
            _validation_entry("silver_fao_food_price_series", normalized_fao, key_columns=["observation_date"]),
            _validation_entry("silver_wgi_country_year_snapshot", normalized_wgi, key_columns=["country_iso3", "year"]),
            _validation_entry("silver_idea_elections", normalized_idea, key_columns=["country_iso3", "election_date", "source_record_id"]),
            _validation_entry("silver_noaa_climate_series", normalized_noaa, key_columns=["country_iso3", "observation_date"]),
            _validation_entry("silver_sipri_security_series", normalized_sipri, key_columns=["country_iso3", "year"]),
            _validation_entry(
                "silver_nasa_black_marble_night_lights",
                normalized_nasa_black_marble,
                key_columns=["country_iso3", "observation_date"],
            ),
            _validation_entry("silver_un_comtrade_trade_series", normalized_un_comtrade, key_columns=["country_iso3", "observation_date"]),
            _validation_entry("silver_unctad_shipping_series", normalized_unctad, key_columns=["country_iso3", "observation_date"]),
            _validation_entry("silver_unhcr_origin_population", normalized_unhcr, key_columns=["country_id", "year"]),
            _validation_entry("silver_ucdp_events", normalized_ucdp, key_columns=["country_iso3", "event_date_start"]),
            _validation_entry("silver_ucdp_interstate_onset", normalized_ucdp_interstate_onset, key_columns=["country_iso3", "year"]),
            _validation_entry("silver_ucdp_intrastate_onset", normalized_ucdp_intrastate_onset, key_columns=["country_iso3", "year"]),
            _validation_entry("silver_wdi_indicator_series", normalized_wdi, key_columns=["country_iso3", "indicator_id", "year"]),
            _validation_entry("gold_country_week_features", gold_country_week_features, key_columns=["country_iso3", "week_start_date"]),
            _validation_entry("gold_entity_day_features", gold_entity_day_features, key_columns=["entity_id", "feature_date"]),
            _validation_entry("gold_entity_day_labels", gold_entity_day_labels, key_columns=["entity_id", "label_date", "horizon_days"]),
            _validation_entry("gold_report_inputs", gold_report_inputs, key_columns=["report_id", "country_iso3", "report_date"]),
            _validation_entry("gold_social_inputs", gold_social_inputs, key_columns=["post_id", "platform_name", "country_iso3", "publish_date"]),
        ],
    }
    validation_report_file = gold_dir / "validation_report.json"
    write_json(validation_report_file, validation_report)

    gold_entity_day_features_validation_report_file = _write_validation_report(
        entity_day_features_dir,
        "gold_entity_day_features",
        gold_entity_day_features,
        key_columns=["entity_id", "feature_date"],
    )
    gold_entity_day_labels_validation_report_file = _write_validation_report(
        entity_day_labels_dir,
        "gold_entity_day_labels",
        gold_entity_day_labels,
        key_columns=["entity_id", "label_date", "horizon_days"],
    )
    gold_report_inputs_validation_report_file = _write_validation_report(
        report_inputs_dir,
        "gold_report_inputs",
        gold_report_inputs,
        key_columns=["report_id", "country_iso3", "report_date"],
    )
    gold_social_inputs_validation_report_file = _write_validation_report(
        social_inputs_dir,
        "gold_social_inputs",
        gold_social_inputs,
        key_columns=["post_id", "platform_name", "country_iso3", "publish_date"],
    )

    return CountryWeekPipelineRunResult(
        raw_manifest_file=raw_manifest_file,
        validation_report_file=validation_report_file,
        gold_country_week_features_file=gold_country_week_features_file,
        gold_entity_day_features_file=gold_entity_day_features_file,
        gold_entity_day_features_validation_report_file=gold_entity_day_features_validation_report_file,
        gold_entity_day_labels_file=gold_entity_day_labels_file,
        gold_entity_day_labels_validation_report_file=gold_entity_day_labels_validation_report_file,
        gold_report_inputs_file=gold_report_inputs_file,
        gold_report_inputs_validation_report_file=gold_report_inputs_validation_report_file,
        gold_social_inputs_file=gold_social_inputs_file,
        gold_social_inputs_validation_report_file=gold_social_inputs_validation_report_file,
    )
