from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FreshnessTier(StrEnum):
    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    CRITICAL = "critical"
    MISSING = "missing"


class PublicationRunProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_name: str
    artifact_path: str
    completed_at: datetime
    model_name: str | None = None


class PublicationTargetProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    training: PublicationRunProvenance
    calibration: PublicationRunProvenance
    backtest: PublicationRunProvenance


class ForecastCountrySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iso3: str
    country_name: str
    region_name: str | None = None
    score: float
    delta: float
    forecast_as_of: date
    freshness_tier: FreshnessTier
    rank: int | None = Field(default=None, ge=1)


class PredictedConflictCountry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iso3: str | None = None
    country_name: str


class PredictedConflictSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    countries: list[PredictedConflictCountry] = Field(default_factory=list)
    summary: str | None = None
    report_slug: str | None = None
    reason_source: Literal["report_inputs", "lead_country", "fallback"]
    target_name: str
    horizon_days: int = Field(ge=1)


class ForecastSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    forecast_as_of: date
    lead_country_iso3: str
    lead_country_name: str
    predicted_conflict: PredictedConflictSnapshot
    primary_target: str
    alert_type: str
    no_clear_leader: bool
    coverage_count: int = Field(ge=0)
    countries: list[ForecastCountrySnapshot] = Field(default_factory=list)


class WebsiteSnapshotManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    snapshot_id: str
    published_at: datetime
    fresh_until: datetime
    stale_after: datetime
    baseline_used: bool
    forecast_as_of: date
    generated_at: datetime
    coverage_count: int = Field(ge=0)
    top_country_iso3: str
    top_country_name: str
    predicted_conflict: PredictedConflictSnapshot
    primary_target: str
    alert_type: str
    model_status: str
    no_clear_leader: bool
    provenance: "PublicationProvenance"


class PublicationProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    onset: PublicationTargetProvenance | None = None
    escalation: PublicationTargetProvenance | None = None
    structural: PublicationTargetProvenance | None = None


class ModelCardMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brier_score: float
    roc_auc: float
    precision_at_10: float
    recall_at_5: float | None = None
    recall_at_10: float | None = None
    episode_recall: float | None = None
    false_alerts_per_true_alert: float | None = None
    no_clear_leader_rate: float | None = None


class ThresholdPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publish_top_n: int = Field(ge=1)
    publish_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    alert_threshold: float = Field(ge=0.0, le=1.0)
    warning_threshold: float = Field(ge=0.0, le=1.0)
    operating_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class ModelCardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    model_version: str
    target_name: str
    horizon_days: int = Field(ge=1)
    published_at: datetime
    stale_after: datetime
    baseline_used: bool
    primary_target: str
    alert_type: str
    model_status: str
    metrics: ModelCardMetrics
    threshold_policy: ThresholdPolicy
    provenance: PublicationProvenance


class WebsiteSnapshotBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: WebsiteSnapshotManifest
    forecast_snapshot: ForecastSnapshot
    model_card: ModelCardPayload


class SiteSnapshotConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_name: str
    preferred_prediction_file: Path
    secondary_prediction_file: Path | None = None
    baseline_prediction_file: Path | None = None
    training_manifest_file: Path
    training_metrics_file: Path
    calibration_metrics_file: Path
    backtest_metrics_file: Path
    secondary_training_manifest_file: Path | None = None
    secondary_training_metrics_file: Path | None = None
    secondary_calibration_metrics_file: Path | None = None
    secondary_backtest_metrics_file: Path | None = None
    structural_training_manifest_file: Path | None = None
    structural_calibration_metrics_file: Path | None = None
    structural_backtest_metrics_file: Path | None = None
    baseline_training_manifest_file: Path | None = None
    baseline_training_metrics_file: Path | None = None
    baseline_calibration_metrics_file: Path | None = None
    baseline_backtest_metrics_file: Path | None = None
    report_inputs_file: Path | None = None
    output_dir: Path
    published_at: datetime | None = None
    fresh_window_days: int = Field(default=10, ge=0)
    stale_window_days: int = Field(default=21, ge=1)
    publish_top_n: int = Field(default=10, ge=1)
    alert_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    warning_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    operating_threshold: float | None = Field(default=0.6, ge=0.0, le=1.0)


__all__ = [
    "FreshnessTier",
    "ForecastCountrySnapshot",
    "ForecastSnapshot",
    "ModelCardMetrics",
    "ModelCardPayload",
    "PredictedConflictCountry",
    "PredictedConflictSnapshot",
    "PublicationProvenance",
    "PublicationRunProvenance",
    "PublicationTargetProvenance",
    "SiteSnapshotConfig",
    "ThresholdPolicy",
    "WebsiteSnapshotBundle",
    "WebsiteSnapshotManifest",
]
