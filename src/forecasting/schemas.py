from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, BaseModel, Field


class UnitOfAnalysis(str, Enum):
    COUNTRY_DAY = "country_day"
    COUNTRY_WEEK = "country_week"
    ADM1_DAY = "adm1_day"


class LabelKind(str, Enum):
    ONSET = "onset"
    ESCALATION = "escalation"
    THRESHOLD = "threshold"


class ModelKind(str, Enum):
    PRIOR_RATE = "prior_rate"
    LOGISTIC_REGRESSION = "logistic_regression"
    ELASTIC_NET = "elastic_net"
    LIGHTGBM = "lightgbm"
    RANDOM_FOREST = "random_forest"


class DatasetSpec(BaseModel):
    entity_id_column: str
    entity_name_column: str
    date_column: str
    unit_of_analysis: UnitOfAnalysis
    feature_columns: list[str]
    group_columns: list[str] = Field(default_factory=list)


class LabelDefinition(BaseModel):
    name: str
    kind: LabelKind
    source_event_column: str
    lookback_days: int = 30
    forecast_threshold: float = 1.0
    quiet_threshold: float | None = None
    growth_multiplier: float = 1.0
    minimum_baseline: float = 0.0


class SplitConfig(BaseModel):
    min_train_periods: int = Field(
        default=120,
        validation_alias=AliasChoices("min_train_periods", "min_train_days"),
    )
    validation_window_periods: int = Field(
        default=30,
        validation_alias=AliasChoices("validation_window_periods", "validation_window_days"),
    )
    step_periods: int = Field(
        default=30,
        validation_alias=AliasChoices("step_periods", "step_days"),
    )
    max_splits: int | None = None


class ModelSpec(BaseModel):
    name: str
    kind: ModelKind
    params: dict[str, Any] = Field(default_factory=dict)


class EnsembleSpec(BaseModel):
    name: str = "weighted_ensemble"
    members: list[str]
    weights: list[float] | None = None


class StructuralPriorSpec(BaseModel):
    prediction_file: Path
    entity_id_column: str = "entity_id"
    date_column: str = "forecast_date"
    score_column: str = "calibrated_probability"
    feature_name: str = "structural_prior_score"


class TrainingConfig(BaseModel):
    run_name: str
    dataset_path: Path
    dataset_spec: DatasetSpec
    target_name: str
    horizon_days: int
    label_column: str | None = None
    next_event_date_column: str | None = None
    split: SplitConfig = Field(default_factory=SplitConfig)
    models: list[ModelSpec]
    primary_model: str
    prediction_threshold: float = 0.5
    seed: int = 7
    label_definition: LabelDefinition | None = None
    ensemble: EnsembleSpec | None = None
    structural_prior: StructuralPriorSpec | None = None


class CalibrationConfig(BaseModel):
    run_name: str
    model_name: str
    method: str = "isotonic"
    score_column: str = "raw_score"
    label_column: str = "label"


class PredictionConfig(BaseModel):
    run_name: str
    dataset_path: Path
    dataset_spec: DatasetSpec
    model_name: str
    top_n_drivers: int = 5
    prediction_output_name: str = "predictions.parquet"
    structural_prior: StructuralPriorSpec | None = None


class ExplanationConfig(BaseModel):
    run_name: str
    model_name: str
    top_n_drivers: int = 5


@dataclass(frozen=True)
class SplitWindow:
    split_id: str
    train_start: date
    train_end: date
    validation_start: date
    validation_end: date


@dataclass(frozen=True)
class TrainingRunResult:
    run_dir: Path
    manifest_file: Path
    metrics_file: Path
    validation_predictions_file: Path


@dataclass(frozen=True)
class CalibrationRunResult:
    run_dir: Path
    calibrator_file: Path
    metrics_file: Path


@dataclass(frozen=True)
class PredictionRunResult:
    run_dir: Path
    prediction_file: Path


@dataclass(frozen=True)
class ExplanationRunResult:
    run_dir: Path
    global_explanations_file: Path
    local_explanations_file: Path
