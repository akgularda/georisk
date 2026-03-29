from __future__ import annotations

from pathlib import Path

import yaml

from src.forecasting.schemas import LabelDefinition


def load_label_definitions(config_path: Path) -> dict[str, LabelDefinition]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    definitions: dict[str, LabelDefinition] = {}
    for item in raw.get("targets", []):
        definition = LabelDefinition.model_validate(item)
        definitions[definition.name] = definition
    return definitions
