from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from src.data_platform.schemas import (
    ArtifactStatus,
    AccessRequirement,
    DataPlatformCatalog,
    GoldServingContract,
    PhaseASourceContract,
    SnapshotRequirement,
    SourceReadiness,
)

DEFAULT_SOURCE_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "configs" / "data_platform" / "source_registry.yaml"


def load_source_registry(path: str | Path | None = None) -> DataPlatformCatalog:
    registry_path = Path(path) if path is not None else DEFAULT_SOURCE_REGISTRY_PATH
    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("source registry must be a mapping")
    return catalog_from_mapping(payload)


def catalog_from_mapping(payload: Mapping[str, Any]) -> DataPlatformCatalog:
    version = int(payload.get("version", 1))
    notes = str(payload.get("notes", "") or "")
    phase_a_sources = tuple(_parse_source_entry(entry) for entry in _require_sequence(payload, "phase_a_sources"))
    serving_contracts = tuple(
        _parse_serving_contract(entry) for entry in _require_sequence(payload, "serving_contracts")
    )
    return DataPlatformCatalog(
        version=version,
        phase_a_sources=phase_a_sources,
        serving_contracts=serving_contracts,
        notes=notes,
    )


def _parse_source_entry(entry: Any) -> PhaseASourceContract:
    if not isinstance(entry, Mapping):
        raise TypeError("phase_a_sources entries must be mappings")
    return PhaseASourceContract(
        key=str(entry["key"]),
        name=str(entry["name"]),
        readiness=SourceReadiness(str(entry["readiness"])),
        access_requirement=AccessRequirement(str(entry["access_requirement"])),
        snapshot_requirement=SnapshotRequirement(str(entry["snapshot_requirement"])),
        category=str(entry["category"]),
        access_pattern=str(entry["access_pattern"]),
        notes=str(entry.get("notes", "") or ""),
        source_urls=_require_tuple(entry, "source_urls"),
    )


def _parse_serving_contract(entry: Any) -> GoldServingContract:
    if not isinstance(entry, Mapping):
        raise TypeError("serving_contracts entries must be mappings")
    return GoldServingContract(
        contract_name=str(entry["contract_name"]),
        artifact_name=str(entry["artifact_name"]),
        status=ArtifactStatus(str(entry["status"])),
        grain=str(entry["grain"]),
        key_columns=_require_tuple(entry, "key_columns"),
        required_columns=_require_tuple(entry, "required_columns"),
        optional_columns=_require_optional_tuple(entry, "optional_columns"),
        notes=str(entry.get("notes", "") or ""),
    )


def _require_sequence(payload: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = payload.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"{key} must be a sequence")
    return value


def _require_tuple(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    return tuple(str(item) for item in _require_sequence(payload, key))


def _require_optional_tuple(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    if key not in payload or payload[key] is None:
        return ()
    return _require_tuple(payload, key)
