from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from src.forecasting.schemas import DatasetSpec, LabelDefinition, ModelSpec, SplitConfig, StructuralPriorSpec


class BacktestConfig(BaseModel):
    run_name: str
    dataset_path: Path
    dataset_spec: DatasetSpec
    target_name: str
    horizon_days: int
    label_column: str | None = None
    next_event_date_column: str | None = None
    label_definition: LabelDefinition | None = None
    split: SplitConfig = Field(default_factory=SplitConfig)
    models: list[ModelSpec]
    primary_model: str
    baseline_model: str | None = None
    prediction_threshold: float = 0.5
    seed: int = 7
    calibration_method: str = "isotonic"
    alert_gap_days: int | None = None
    structural_prior: StructuralPriorSpec | None = None


class ReplayConfig(BaseModel):
    run_name: str
    backtest_run_name: str
    entity_id: str
    model_name: str | None = None
    max_rows: int = 20


@dataclass(frozen=True)
class BacktestRunResult:
    run_dir: Path
    predictions_file: Path
    alerts_file: Path
    metrics_file: Path
    report_file: Path
    windows_file: Path


@dataclass(frozen=True)
class ReplayRunResult:
    run_dir: Path
    replay_file: Path
