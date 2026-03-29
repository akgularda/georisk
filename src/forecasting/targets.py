from __future__ import annotations

from pathlib import Path

from src.forecasting.label_configs import load_label_definitions
from src.forecasting.schemas import LabelDefinition, LabelKind
from src.forecasting.utils import project_root


DEFAULT_TARGETS: dict[str, LabelDefinition] = {
    "organized_violence_onset": LabelDefinition(
        name="organized_violence_onset",
        kind=LabelKind.ONSET,
        source_event_column="organized_violence_events",
        lookback_days=30,
        quiet_threshold=0.0,
        forecast_threshold=3.0,
    ),
    "organized_violence_escalation": LabelDefinition(
        name="organized_violence_escalation",
        kind=LabelKind.ESCALATION,
        source_event_column="organized_violence_events",
        lookback_days=30,
        forecast_threshold=5.0,
        growth_multiplier=1.5,
    ),
    "major_unrest_escalation": LabelDefinition(
        name="major_unrest_escalation",
        kind=LabelKind.ESCALATION,
        source_event_column="protest_events",
        lookback_days=30,
        forecast_threshold=6.0,
        growth_multiplier=1.5,
    ),
    "interstate_confrontation_risk": LabelDefinition(
        name="interstate_confrontation_risk",
        kind=LabelKind.THRESHOLD,
        source_event_column="interstate_tension_events",
        lookback_days=30,
        forecast_threshold=2.0,
    ),
    "humanitarian_deterioration_risk": LabelDefinition(
        name="humanitarian_deterioration_risk",
        kind=LabelKind.THRESHOLD,
        source_event_column="humanitarian_displacement_flow",
        lookback_days=30,
        forecast_threshold=150.0,
    ),
}


def get_label_definition(target_name: str) -> LabelDefinition:
    config_path = project_root() / "configs" / "forecasting" / "label_definitions.yaml"
    if config_path.exists():
        definitions = load_label_definitions(Path(config_path))
        if target_name in definitions:
            return definitions[target_name]
    try:
        return DEFAULT_TARGETS[target_name].model_copy(deep=True)
    except KeyError as exc:
        raise ValueError(f"Unknown target: {target_name}") from exc
