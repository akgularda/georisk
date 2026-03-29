from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_path(path_value: str | Path, base_path: Path | None = None) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    if base_path is None:
        base_path = project_root()
    return (base_path / path).resolve()


def load_yaml_config(config_path: Path, model_cls: type[T]) -> T:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if "dataset_path" in raw:
        raw["dataset_path"] = str(resolve_path(raw["dataset_path"], config_path.parent.parent.parent))
    return model_cls.model_validate(raw)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_feature_hash(feature_values: dict[str, Any]) -> str:
    content = json.dumps(feature_values, sort_keys=True, default=str)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

