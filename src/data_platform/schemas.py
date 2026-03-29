from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class SourceReadiness(StrEnum):
    implemented = "implemented"
    stubbed = "stubbed"
    missing = "missing"


class AccessRequirement(StrEnum):
    open = "open"
    account_required = "account_required"


class SnapshotRequirement(StrEnum):
    none = "none"
    snapshot_required = "snapshot_required"


SourceStatus = SourceReadiness


class ArtifactStatus(StrEnum):
    implemented = "implemented"
    stubbed = "stubbed"
    missing = "missing"


class GDELTConfig(BaseModel):
    lastupdate_url: str = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    masterfile_url: str = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
    export_file_limit: int = 24
    gkg_file_limit: int = 4


class UNHCRConfig(BaseModel):
    population_base_url: str = "https://api.unhcr.org/population/v1/population/"
    population_origin_year: int = 2024
    page_size: int = 500


class WDIConfig(BaseModel):
    api_base_url: str = "https://api.worldbank.org/v2"
    country_selector: str = "all"
    per_page: int = 20000
    mrv: int = 10
    indicators: dict[str, str] = Field(
        default_factory=lambda: {
            "macro_gdp_growth_annual_pct": "NY.GDP.MKTP.KD.ZG",
            "macro_cpi_yoy": "FP.CPI.TOTL.ZG",
            "macro_population_total": "SP.POP.TOTL",
        }
    )


class IMFConfig(BaseModel):
    snapshot_file: Path
    publication_ts_utc: datetime = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


class FAOConfig(BaseModel):
    snapshot_file: Path
    publication_ts_utc: datetime = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


class WGIConfig(BaseModel):
    snapshot_file: Path
    publication_ts_utc: datetime = datetime(2025, 9, 15, 0, 0, 0, tzinfo=timezone.utc)


class NOAAConfig(BaseModel):
    snapshot_file: Path
    publication_ts_utc: datetime = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


class SIPRIConfig(BaseModel):
    snapshot_file: Path
    publication_ts_utc: datetime = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


class NASABlackMarbleConfig(BaseModel):
    snapshot_file: Path
    publication_ts_utc: datetime = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


class IDEAConfig(BaseModel):
    snapshot_file: Path


class UNComtradeConfig(BaseModel):
    snapshot_file: Path
    publication_ts_utc: datetime = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


class UNCTADConfig(BaseModel):
    snapshot_file: Path
    publication_ts_utc: datetime = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


class UCDPConfig(BaseModel):
    download_url: str = "https://ucdp.uu.se/downloads/ged/ged251-csv.zip"
    min_year: int = 2015


class UCDPOnsetConfig(BaseModel):
    interstate_download_url: str = "https://ucdp.uu.se/downloads/onset/ucdp-interstate-country-onset-251.csv"
    intrastate_download_url: str = "https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-onset-251.csv"


class ACLEDConfig(BaseModel):
    snapshot_file: Path


class StorageConfig(BaseModel):
    storage_root: Path = Path("data")


class CountryWeekPanelConfig(BaseModel):
    start_date: date = date(2015, 1, 5)
    end_date: date | None = None


class LiveCountrySignalsConfig(BaseModel):
    pipeline_kind: str = "live_country_signals"
    run_name: str
    storage: StorageConfig = Field(default_factory=StorageConfig)
    gdelt: GDELTConfig = Field(default_factory=GDELTConfig)
    unhcr: UNHCRConfig = Field(default_factory=UNHCRConfig)


class CountryWeekFeaturesConfig(BaseModel):
    pipeline_kind: str = "country_week_features"
    run_name: str
    storage: StorageConfig = Field(default_factory=StorageConfig)
    panel: CountryWeekPanelConfig = Field(default_factory=CountryWeekPanelConfig)
    acled: ACLEDConfig
    fao: FAOConfig
    gdelt: GDELTConfig = Field(default_factory=GDELTConfig)
    idea: IDEAConfig
    imf: IMFConfig
    nasa_black_marble: NASABlackMarbleConfig
    noaa: NOAAConfig
    sipri: SIPRIConfig
    un_comtrade: UNComtradeConfig
    unctad: UNCTADConfig
    unhcr: UNHCRConfig = Field(default_factory=UNHCRConfig)
    wdi: WDIConfig = Field(default_factory=WDIConfig)
    wgi: WGIConfig
    ucdp: UCDPConfig = Field(default_factory=UCDPConfig)
    ucdp_onset: UCDPOnsetConfig = Field(default_factory=UCDPOnsetConfig)


@dataclass(frozen=True)
class GDELTLastUpdate:
    export_size_bytes: int
    export_md5: str
    export_url: str
    mentions_size_bytes: int
    mentions_md5: str
    mentions_url: str
    gkg_size_bytes: int
    gkg_md5: str
    gkg_url: str


@dataclass(frozen=True)
class PipelineRunResult:
    raw_manifest_file: Path
    validation_report_file: Path
    gold_country_signals_file: Path


@dataclass(frozen=True)
class CountryWeekPipelineRunResult:
    raw_manifest_file: Path
    validation_report_file: Path
    gold_country_week_features_file: Path
    gold_entity_day_features_file: Path
    gold_entity_day_features_validation_report_file: Path
    gold_entity_day_labels_file: Path
    gold_entity_day_labels_validation_report_file: Path
    gold_report_inputs_file: Path
    gold_report_inputs_validation_report_file: Path
    gold_social_inputs_file: Path
    gold_social_inputs_validation_report_file: Path


@dataclass(frozen=True)
class PhaseASourceContract:
    key: str
    name: str
    readiness: SourceReadiness
    access_requirement: AccessRequirement
    snapshot_requirement: SnapshotRequirement
    category: str
    access_pattern: str
    notes: str = ""
    source_urls: tuple[str, ...] = ()

    @property
    def status(self) -> SourceReadiness:
        return self.readiness


@dataclass(frozen=True)
class GoldServingContract:
    contract_name: str
    artifact_name: str
    status: ArtifactStatus
    grain: str
    key_columns: tuple[str, ...]
    required_columns: tuple[str, ...]
    optional_columns: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class DataPlatformCatalog:
    version: int
    phase_a_sources: tuple[PhaseASourceContract, ...]
    serving_contracts: tuple[GoldServingContract, ...]
    notes: str = ""

    def __post_init__(self) -> None:
        if len({source.key for source in self.phase_a_sources}) != len(self.phase_a_sources):
            raise ValueError("phase_a_sources must not contain duplicate keys")
        if len({contract.contract_name for contract in self.serving_contracts}) != len(self.serving_contracts):
            raise ValueError("serving_contracts must not contain duplicate contract names")

    def source_by_key(self, key: str) -> PhaseASourceContract:
        for source in self.phase_a_sources:
            if source.key == key:
                return source
        raise KeyError(key)

    def serving_contract_by_name(self, contract_name: str) -> GoldServingContract:
        for contract in self.serving_contracts:
            if contract.contract_name == contract_name:
                return contract
        raise KeyError(contract_name)

    def source_keys(self) -> tuple[str, ...]:
        return tuple(source.key for source in self.phase_a_sources)

    def serving_contract_names(self) -> tuple[str, ...]:
        return tuple(contract.contract_name for contract in self.serving_contracts)
