from __future__ import annotations

from pathlib import Path

from src.forecasting.label_configs import load_label_definitions


def test_label_definitions_can_be_loaded_from_yaml() -> None:
    project_root = Path(__file__).resolve().parents[3]
    definitions = load_label_definitions(project_root / "configs" / "forecasting" / "label_definitions.yaml")

    assert "organized_violence_onset" in definitions
    assert definitions["organized_violence_onset"].source_event_column == "organized_violence_events"
    assert definitions["humanitarian_deterioration_risk"].forecast_threshold >= 150.0

