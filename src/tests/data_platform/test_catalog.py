from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from src.data_platform.catalog import DEFAULT_SOURCE_REGISTRY_PATH, catalog_from_mapping, load_source_registry
from src.data_platform.schemas import AccessRequirement, ArtifactStatus, SnapshotRequirement, SourceReadiness


def _registry_payload() -> dict:
    return yaml.safe_load(Path(DEFAULT_SOURCE_REGISTRY_PATH).read_text(encoding="utf-8"))


def test_load_source_registry_matches_phase_a_contract() -> None:
    catalog = load_source_registry(DEFAULT_SOURCE_REGISTRY_PATH)

    assert catalog.version == 1
    assert catalog.source_keys() == (
        "acled",
        "ucdp_ged",
        "ucdp_onset",
        "gdelt",
        "unhcr",
        "wdi",
        "imf",
        "fao",
        "vdem",
        "wgi",
        "idea",
        "sipri",
        "unctad",
        "noaa",
        "nasa_black_marble",
        "un_comtrade",
    )
    assert catalog.source_by_key("acled").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("acled").access_requirement is AccessRequirement.account_required
    assert catalog.source_by_key("acled").snapshot_requirement is SnapshotRequirement.none
    assert catalog.source_by_key("ucdp_ged").snapshot_requirement is SnapshotRequirement.snapshot_required
    assert catalog.source_by_key("wgi").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("idea").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("imf").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("imf").snapshot_requirement is SnapshotRequirement.snapshot_required
    assert catalog.source_by_key("fao").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("fao").snapshot_requirement is SnapshotRequirement.snapshot_required
    assert catalog.source_by_key("unctad").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("unctad").snapshot_requirement is SnapshotRequirement.snapshot_required
    assert catalog.source_by_key("sipri").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("sipri").snapshot_requirement is SnapshotRequirement.snapshot_required
    assert catalog.source_by_key("noaa").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("noaa").snapshot_requirement is SnapshotRequirement.snapshot_required
    assert catalog.source_by_key("nasa_black_marble").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("nasa_black_marble").snapshot_requirement is SnapshotRequirement.snapshot_required
    assert catalog.source_by_key("un_comtrade").readiness is SourceReadiness.implemented
    assert catalog.source_by_key("un_comtrade").snapshot_requirement is SnapshotRequirement.snapshot_required

    assert catalog.serving_contract_names() == (
        "gold_country_week_features",
        "gold_entity_day_features",
        "gold_entity_day_labels",
        "gold_report_inputs",
        "gold_social_inputs",
    )
    assert catalog.serving_contract_by_name("gold_country_week_features").status is ArtifactStatus.implemented
    assert catalog.serving_contract_by_name("gold_entity_day_features").status is ArtifactStatus.implemented
    assert catalog.serving_contract_by_name("gold_entity_day_labels").status is ArtifactStatus.implemented
    assert catalog.serving_contract_by_name("gold_report_inputs").status is ArtifactStatus.implemented
    assert catalog.serving_contract_by_name("gold_social_inputs").status is ArtifactStatus.implemented
    assert catalog.serving_contract_by_name("gold_entity_day_labels").key_columns == (
        "entity_id",
        "label_date",
        "horizon_days",
    )
    assert catalog.serving_contract_by_name("gold_entity_day_features").required_columns == (
        "entity_id",
        "entity_type",
        "country_iso3",
        "country_name",
        "feature_date",
        "source_week_start_date",
    )
    assert catalog.serving_contract_by_name("gold_entity_day_labels").required_columns == (
        "entity_id",
        "country_iso3",
        "label_date",
        "horizon_days",
        "label_escalation_7d",
        "label_escalation_30d",
        "label_onset_30d",
        "label_onset_90d",
        "label_interstate_onset_30d",
        "label_interstate_onset_90d",
    )
    assert catalog.serving_contract_by_name("gold_report_inputs").key_columns == (
        "country_iso3",
        "report_date",
    )
    assert catalog.serving_contract_by_name("gold_report_inputs").required_columns == (
        "country_iso3",
        "country_name",
        "region_name",
        "report_date",
        "risk_level",
        "freshness_days",
        "summary",
        "chronology",
    )
    assert catalog.serving_contract_by_name("gold_social_inputs").key_columns == (
        "country_iso3",
        "publish_date",
    )
    assert catalog.serving_contract_by_name("gold_social_inputs").required_columns == (
        "country_iso3",
        "country_name",
        "publish_date",
        "score_delta",
        "summary_line",
        "top_drivers",
        "report_slug",
    )
    assert catalog.serving_contract_by_name("gold_social_inputs").artifact_name == "social_inputs"


def test_catalog_rejects_duplicate_source_keys() -> None:
    payload = _registry_payload()
    payload["phase_a_sources"] = payload["phase_a_sources"][:2] + [deepcopy(payload["phase_a_sources"][0])]

    with pytest.raises(ValueError, match="duplicate keys"):
        catalog_from_mapping(payload)


def test_catalog_rejects_duplicate_serving_contract_names() -> None:
    payload = _registry_payload()
    payload["serving_contracts"] = payload["serving_contracts"][:2] + [deepcopy(payload["serving_contracts"][0])]

    with pytest.raises(ValueError, match="duplicate contract names"):
        catalog_from_mapping(payload)


@pytest.mark.parametrize(
    ("section", "entry_index", "missing_key", "match"),
    [
        ("phase_a_sources", 0, "category", r"'category'"),
        ("phase_a_sources", 0, "readiness", r"'readiness'"),
        ("serving_contracts", 0, "artifact_name", r"'artifact_name'"),
        ("serving_contracts", 0, "grain", r"'grain'"),
    ],
)
def test_catalog_rejects_missing_required_fields(
    section: str, entry_index: int, missing_key: str, match: str
) -> None:
    payload = _registry_payload()
    del payload[section][entry_index][missing_key]

    with pytest.raises(KeyError, match=match):
        catalog_from_mapping(payload)


@pytest.mark.parametrize(
    ("section", "entry_index", "field_name"),
    [
        ("phase_a_sources", 0, "source_urls"),
        ("serving_contracts", 0, "key_columns"),
        ("serving_contracts", 0, "required_columns"),
        ("serving_contracts", 0, "optional_columns"),
    ],
)
def test_catalog_rejects_malformed_list_fields(section: str, entry_index: int, field_name: str) -> None:
    payload = _registry_payload()
    payload[section][entry_index][field_name] = "not-a-sequence"

    with pytest.raises(TypeError, match="must be a sequence"):
        catalog_from_mapping(payload)
