from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from src.forecasting.utils import write_json
from src.website_publishing.schemas import (
    ForecastCountrySnapshot,
    ForecastSnapshot,
    FreshnessTier,
    ModelCardMetrics,
    ModelCardPayload,
    PredictedConflictCountry,
    PredictedConflictSnapshot,
    PublicationProvenance,
    PublicationRunProvenance,
    PublicationTargetProvenance,
    SiteSnapshotConfig,
    ThresholdPolicy,
    WebsiteSnapshotBundle,
    WebsiteSnapshotManifest,
)


@dataclass(frozen=True)
class SiteSnapshotRunResult:
    output_dir: Path
    manifest_file: Path
    forecast_snapshot_file: Path
    backtest_summary_file: Path
    model_card_file: Path
    status_file: Path
    country_dir: Path


def _as_utc_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = pd.Timestamp(value).to_pydatetime()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _as_date(value: object) -> date:
    return pd.Timestamp(value).date()


def _path_completed_at(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_driver_labels(raw_value: object) -> list[str]:
    if raw_value is None or pd.isna(raw_value):
        return []
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value]
    try:
        parsed = json.loads(str(raw_value))
    except json.JSONDecodeError:
        return [str(raw_value)]
    if isinstance(parsed, list):
        labels: list[str] = []
        for item in parsed:
            if isinstance(item, dict):
                feature = item.get("feature")
                if feature is not None:
                    labels.append(str(feature))
            else:
                labels.append(str(item))
        return labels
    return [str(parsed)]


def _freshness_tier(
    *,
    reference_time: datetime,
    snapshot_time: datetime,
    fresh_window_days: int,
    stale_window_days: int,
) -> FreshnessTier:
    age_days = max((reference_time - snapshot_time).total_seconds() / 86400.0, 0.0)
    if age_days <= fresh_window_days:
        return FreshnessTier.FRESH
    if age_days <= stale_window_days:
        return FreshnessTier.AGING
    return FreshnessTier.STALE


def _load_prediction_frame_with_fallback(config: SiteSnapshotConfig) -> tuple[pd.DataFrame, Path, bool]:
    attempted_paths: list[str] = []
    load_errors: list[str] = []

    if config.preferred_prediction_file.exists():
        attempted_paths.append(str(config.preferred_prediction_file))
        try:
            return _load_prediction_frame(config.preferred_prediction_file), config.preferred_prediction_file, False
        except (OSError, ValueError) as error:
            load_errors.append(f"preferred={config.preferred_prediction_file}: {error}")

    baseline_file = config.baseline_prediction_file
    if baseline_file is not None and baseline_file.exists():
        attempted_paths.append(str(baseline_file))
        try:
            return _load_prediction_frame(baseline_file), baseline_file, True
        except (OSError, ValueError) as error:
            load_errors.append(f"baseline={baseline_file}: {error}")

    attempted = ", ".join(attempted_paths) if attempted_paths else "none"
    if load_errors:
        raise ValueError(
            "No usable prediction artifact is available. "
            f"Attempted paths: {attempted}. Errors: {' | '.join(load_errors)}"
        )
    raise FileNotFoundError(
        "No prediction artifact is available. "
        f"Tried preferred={config.preferred_prediction_file} and baseline={config.baseline_prediction_file}."
    )


def _load_prediction_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    required_columns = {
        "country_iso3",
        "country_name",
        "forecast_date",
        "calibrated_probability",
        "model_name",
        "model_version",
        "target_name",
        "horizon_days",
    }
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Prediction artifact is missing required columns: {missing}")
    frame = frame.copy()
    frame["forecast_date"] = pd.to_datetime(frame["forecast_date"], errors="coerce")
    frame["calibrated_probability"] = pd.to_numeric(frame["calibrated_probability"], errors="coerce")
    if "raw_score" in frame.columns:
        frame["raw_score"] = pd.to_numeric(frame["raw_score"], errors="coerce")
    if "snapshot_ts_utc" in frame.columns:
        frame["snapshot_ts_utc"] = pd.to_datetime(frame["snapshot_ts_utc"], utc=True, errors="coerce")
    invalid_value_mask = frame["forecast_date"].isna() | frame["calibrated_probability"].isna()
    if invalid_value_mask.any():
        invalid_count = int(invalid_value_mask.sum())
        raise ValueError(
            "Prediction artifact contains invalid required values "
            f"for forecast_date or calibrated_probability in {invalid_count} row(s)."
        )
    return frame.sort_values(["country_iso3", "forecast_date"]).reset_index(drop=True)


def _build_country_snapshots(
    prediction_frame: pd.DataFrame,
    *,
    freshness_tier: FreshnessTier,
) -> tuple[list[ForecastCountrySnapshot], datetime, date, int]:
    latest_rows = prediction_frame.sort_values(["country_iso3", "forecast_date"]).groupby("country_iso3", sort=False).tail(1).copy()
    snapshot_values = (
        latest_rows["snapshot_ts_utc"].dropna() if "snapshot_ts_utc" in latest_rows.columns else pd.Series(dtype="datetime64[ns, UTC]")
    )
    latest_snapshot_time = (
        snapshot_values.max().to_pydatetime().astimezone(UTC)
        if not snapshot_values.empty
        else latest_rows["forecast_date"].max().to_pydatetime().replace(tzinfo=UTC)
    )
    forecast_as_of = latest_rows["forecast_date"].max().date()
    secondary_score = latest_rows["raw_score"] if "raw_score" in latest_rows.columns else latest_rows["calibrated_probability"]
    ordered_rows = latest_rows.assign(
        _secondary_score=secondary_score.fillna(float("-inf")),
        _country_name=latest_rows["country_name"].fillna(""),
        _iso3=latest_rows["country_iso3"].fillna(""),
    ).sort_values(
        by=["calibrated_probability", "_secondary_score", "_country_name", "_iso3"],
        ascending=[False, False, True, True],
        kind="mergesort",
    )
    snapshots: list[ForecastCountrySnapshot] = []

    for _, latest in ordered_rows.iterrows():
        country_history = prediction_frame.loc[prediction_frame["country_iso3"] == latest["country_iso3"]].sort_values("forecast_date").reset_index(drop=True)
        previous_score = (
            float(country_history.iloc[-2]["calibrated_probability"])
            if len(country_history) > 1 and not pd.isna(country_history.iloc[-2]["calibrated_probability"])
            else float(latest["calibrated_probability"])
        )
        snapshots.append(
            ForecastCountrySnapshot(
                iso3=str(latest["country_iso3"]),
                country_name=str(latest["country_name"]),
                region_name=None if pd.isna(latest.get("region_name")) else str(latest.get("region_name")),
                score=round(float(latest["calibrated_probability"]), 4),
                delta=round(float(latest["calibrated_probability"]) - previous_score, 4),
                forecast_as_of=forecast_as_of,
                freshness_tier=freshness_tier,
            )
        )

    with_ranks = [
        snapshot.model_copy(update={"rank": rank})
        for rank, snapshot in enumerate(snapshots, start=1)
    ]
    lead_score = float(ordered_rows.iloc[0]["calibrated_probability"])
    lead_tie_count = int((latest_rows["calibrated_probability"] == lead_score).sum())
    return with_ranks, latest_snapshot_time, forecast_as_of, lead_tie_count


def _load_report_inputs(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path).copy()


def _parse_predicted_conflict_countries(raw_value: object) -> list[PredictedConflictCountry]:
    if raw_value is None or pd.isna(raw_value):
        return []
    if isinstance(raw_value, list):
        parsed = raw_value
    else:
        try:
            parsed = json.loads(str(raw_value))
        except json.JSONDecodeError:
            return []
    if not isinstance(parsed, list):
        return []

    countries: list[PredictedConflictCountry] = []
    for item in parsed:
        if isinstance(item, dict):
            country_name = item.get("country_name") or item.get("name")
            if country_name is None:
                continue
            iso3 = item.get("iso3")
            countries.append(
                PredictedConflictCountry(
                    iso3=None if iso3 is None else str(iso3),
                    country_name=str(country_name),
                )
            )
        elif item is not None:
            countries.append(PredictedConflictCountry(country_name=str(item)))
    return countries


def _build_predicted_conflict(
    snapshots: list[ForecastCountrySnapshot],
    report_inputs: pd.DataFrame,
    *,
    target_name: str,
    horizon_days: int,
) -> PredictedConflictSnapshot:
    lead_snapshot = snapshots[0]
    default_countries = [
        PredictedConflictCountry(
            iso3=lead_snapshot.iso3,
            country_name=lead_snapshot.country_name,
        )
    ]

    if report_inputs.empty:
        return PredictedConflictSnapshot(
            label=lead_snapshot.country_name,
            countries=default_countries,
            summary=None,
            report_slug=None,
            reason_source="lead_country",
            target_name=target_name,
            horizon_days=horizon_days,
        )

    report_rows = {str(row["country_iso3"]): row for _, row in report_inputs.iterrows()}
    report_row = report_rows.get(lead_snapshot.iso3)
    if report_row is None:
        return PredictedConflictSnapshot(
            label=lead_snapshot.country_name,
            countries=default_countries,
            summary=None,
            report_slug=None,
            reason_source="lead_country",
            target_name=target_name,
            horizon_days=horizon_days,
        )

    explicit_countries = _parse_predicted_conflict_countries(report_row.get("predicted_conflict_countries"))
    chronology = _parse_driver_labels(report_row.get("chronology"))
    summary = None if pd.isna(report_row.get("summary")) else str(report_row.get("summary"))
    report_title = None if pd.isna(report_row.get("report_title")) else str(report_row.get("report_title"))
    text_blob = " ".join(filter(None, [report_title, summary, *chronology])).casefold()
    detected_countries: list[PredictedConflictCountry] = []
    for snapshot in snapshots[:10]:
        if snapshot.country_name.casefold() in text_blob:
            detected_countries.append(
                PredictedConflictCountry(
                    iso3=snapshot.iso3,
                    country_name=snapshot.country_name,
                )
            )
    if not any(country.country_name == lead_snapshot.country_name for country in detected_countries):
        detected_countries.insert(
            0,
            PredictedConflictCountry(
                iso3=lead_snapshot.iso3,
                country_name=lead_snapshot.country_name,
            ),
        )

    countries = explicit_countries or detected_countries or default_countries
    explicit_label = None if pd.isna(report_row.get("predicted_conflict_label")) else str(report_row.get("predicted_conflict_label")).strip()
    label = explicit_label or " / ".join(country.country_name for country in countries)
    raw_reason_source = None if pd.isna(report_row.get("reason_source")) else str(report_row.get("reason_source")).strip()
    reason_source = raw_reason_source if raw_reason_source in {"report_inputs", "lead_country", "fallback"} else "report_inputs"

    return PredictedConflictSnapshot(
        label=label,
        countries=countries,
        summary=summary,
        report_slug=None if pd.isna(report_row.get("report_slug")) else str(report_row.get("report_slug")),
        reason_source=reason_source,
        target_name=target_name,
        horizon_days=horizon_days,
    )


def _build_country_detail_payloads(
    snapshots: list[ForecastCountrySnapshot],
    prediction_frame: pd.DataFrame,
    report_inputs: pd.DataFrame,
    *,
    model_name: str,
    model_version: str,
    target_name: str,
    horizon_days: int,
) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    report_rows = {str(row["country_iso3"]): row for _, row in report_inputs.iterrows()} if not report_inputs.empty else {}

    for snapshot in snapshots:
        country_history = prediction_frame.loc[prediction_frame["country_iso3"] == snapshot.iso3].sort_values("forecast_date")
        latest_prediction = country_history.iloc[-1]
        report_row = report_rows.get(snapshot.iso3)
        chronology = []
        top_drivers: list[str] = _parse_driver_labels(latest_prediction.get("top_positive_drivers"))
        summary = None
        report_slug = None
        source_snapshot_hash = None
        if report_row is not None:
            report_slug = str(report_row.get("report_slug"))
            summary = str(report_row.get("summary"))
            chronology = _parse_driver_labels(report_row.get("chronology"))
            report_drivers = _parse_driver_labels(report_row.get("top_drivers_json") or report_row.get("top_drivers"))
            if report_drivers:
                top_drivers = report_drivers
            source_snapshot_hash = None if pd.isna(report_row.get("source_snapshot_hash")) else str(report_row.get("source_snapshot_hash"))

        payloads[snapshot.iso3.lower()] = {
            "iso3": snapshot.iso3,
            "country_name": snapshot.country_name,
            "region_name": snapshot.region_name,
            "report_slug": report_slug,
            "summary": summary,
            "chronology": chronology,
            "top_drivers": top_drivers,
            "forecast": {
                "score": snapshot.score,
                "delta": snapshot.delta,
                "rank": snapshot.rank,
                "forecast_as_of": snapshot.forecast_as_of.isoformat(),
                "freshness_tier": snapshot.freshness_tier.value,
                "model_name": model_name,
                "model_version": model_version,
                "target_name": target_name,
                "horizon_days": horizon_days,
            },
            "source_snapshot_hash": source_snapshot_hash
            or (None if pd.isna(latest_prediction.get("feature_snapshot_hash")) else str(latest_prediction.get("feature_snapshot_hash"))),
        }
    return payloads


def _normalize_target_name(target_name: str) -> str:
    normalized = target_name.strip().lower()
    if "onset" in normalized:
        return "onset"
    if "escalation" in normalized:
        return "escalation"
    return normalized


def _build_target_provenance(
    *,
    training_manifest_file: Path,
    training_manifest: dict[str, Any],
    calibration_metrics_file: Path,
    calibration_metrics: dict[str, Any],
    backtest_metrics_file: Path,
    backtest_metrics: dict[str, Any],
) -> PublicationTargetProvenance:
    return PublicationTargetProvenance(
        training=PublicationRunProvenance(
            run_name=str(training_manifest["run_name"]),
            artifact_path=str(training_manifest_file.parent),
            completed_at=_path_completed_at(training_manifest_file),
            model_name=str(training_manifest.get("primary_model")) if training_manifest.get("primary_model") is not None else None,
        ),
        calibration=PublicationRunProvenance(
            run_name=str(calibration_metrics["run_name"]),
            artifact_path=str(calibration_metrics_file.parent),
            completed_at=_path_completed_at(calibration_metrics_file),
            model_name=str(calibration_metrics.get("model_name")) if calibration_metrics.get("model_name") is not None else None,
        ),
        backtest=PublicationRunProvenance(
            run_name=str(backtest_metrics_file.parent.name),
            artifact_path=str(backtest_metrics_file.parent),
            completed_at=_path_completed_at(backtest_metrics_file),
            model_name=str(backtest_metrics.get("primary_model")) if backtest_metrics.get("primary_model") is not None else None,
        ),
    )


def _secondary_metadata_files(
    config: SiteSnapshotConfig,
) -> tuple[Path, Path, Path, Path] | None:
    values = {
        "secondary_training_manifest_file": config.secondary_training_manifest_file,
        "secondary_training_metrics_file": config.secondary_training_metrics_file,
        "secondary_calibration_metrics_file": config.secondary_calibration_metrics_file,
        "secondary_backtest_metrics_file": config.secondary_backtest_metrics_file,
    }
    if all(value is None for value in values.values()):
        return None
    missing = [name for name, value in values.items() if value is None]
    if missing:
        raise ValueError(
            "Secondary target publication requires a complete metadata set. "
            f"Missing: {', '.join(sorted(missing))}"
        )
    return (
        config.secondary_training_manifest_file,
        config.secondary_training_metrics_file,
        config.secondary_calibration_metrics_file,
        config.secondary_backtest_metrics_file,
    )


def _publication_provenance(
    *,
    primary_target_name: str,
    primary_target_provenance: PublicationTargetProvenance,
    secondary_target_name: str | None = None,
    secondary_target_provenance: PublicationTargetProvenance | None = None,
    structural_target_provenance: PublicationTargetProvenance | None = None,
) -> PublicationProvenance:
    target_map: dict[str, PublicationTargetProvenance | None] = {
        "onset": None,
        "escalation": None,
    }
    target_map[_normalize_target_name(primary_target_name)] = primary_target_provenance
    if secondary_target_name is not None:
        target_map[_normalize_target_name(secondary_target_name)] = secondary_target_provenance
    return PublicationProvenance(
        onset=target_map["onset"],
        escalation=target_map["escalation"],
        structural=structural_target_provenance,
    )


def _structural_metadata_files(
    config: SiteSnapshotConfig,
) -> tuple[Path, Path, Path] | None:
    values = {
        "structural_training_manifest_file": config.structural_training_manifest_file,
        "structural_calibration_metrics_file": config.structural_calibration_metrics_file,
        "structural_backtest_metrics_file": config.structural_backtest_metrics_file,
    }
    if all(value is None for value in values.values()):
        return None
    missing = [name for name, value in values.items() if value is None]
    if missing:
        raise ValueError(
            "Structural target publication requires a complete metadata set. "
            f"Missing: {', '.join(sorted(missing))}"
        )
    return (
        config.structural_training_manifest_file,
        config.structural_calibration_metrics_file,
        config.structural_backtest_metrics_file,
    )


def _select_metadata_files(
    config: SiteSnapshotConfig,
    *,
    baseline_used: bool,
) -> tuple[Path, Path, Path, Path]:
    if not baseline_used:
        return (
            config.training_manifest_file,
            config.training_metrics_file,
            config.calibration_metrics_file,
            config.backtest_metrics_file,
        )

    required = {
        "baseline_training_manifest_file": config.baseline_training_manifest_file,
        "baseline_training_metrics_file": config.baseline_training_metrics_file,
        "baseline_calibration_metrics_file": config.baseline_calibration_metrics_file,
        "baseline_backtest_metrics_file": config.baseline_backtest_metrics_file,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise ValueError(
            "Baseline fallback requires explicit baseline metadata files. "
            f"Missing: {', '.join(sorted(missing))}"
        )
    return (
        config.baseline_training_manifest_file,
        config.baseline_training_metrics_file,
        config.baseline_calibration_metrics_file,
        config.baseline_backtest_metrics_file,
    )


def _resolve_publication_state(
    *,
    target_name: str,
    lead_score: float,
    second_score: float | None,
    lead_tie_count: int,
    baseline_used: bool,
    primary_model_name: str | None,
    top_model_name: str | None,
    publish_threshold: float | None,
) -> tuple[str, str, bool]:
    primary_target = _normalize_target_name(target_name)
    no_clear_leader = False
    if publish_threshold is not None and lead_score < publish_threshold:
        no_clear_leader = True
    if lead_tie_count > 1:
        no_clear_leader = True
    if second_score is not None and (lead_score - second_score) < 0.02:
        no_clear_leader = True

    model_status = "promoted"
    if baseline_used or primary_model_name is None or top_model_name is None or top_model_name != primary_model_name:
        model_status = "monitoring_only"

    if no_clear_leader:
        alert_type = "No Clear Leader"
    elif model_status != "promoted":
        alert_type = "Monitoring Only"
    elif primary_target == "onset":
        alert_type = "Onset Watch"
    elif primary_target == "escalation":
        alert_type = "Escalation Watch"
    else:
        alert_type = "Monitoring Only"

    return primary_target, alert_type, no_clear_leader


def _build_model_card(
    *,
    selected_model_name: str,
    model_version: str,
    training_manifest: dict[str, Any],
    training_metrics: dict[str, Any],
    backtest_metrics: dict[str, Any],
    provenance: PublicationProvenance,
    published_at: datetime,
    stale_after: datetime,
    baseline_used: bool,
    primary_target: str,
    alert_type: str,
    model_status: str,
    publish_top_n: int,
    alert_threshold: float,
    warning_threshold: float,
    operating_threshold: float | None,
) -> ModelCardPayload:
    overall_metrics = training_metrics["models"][selected_model_name]["overall"]
    alert_metrics = backtest_metrics.get("alerts", {})
    return ModelCardPayload(
        model_name=selected_model_name,
        model_version=model_version,
        target_name=str(training_manifest["target_name"]),
        horizon_days=int(training_manifest["horizon_days"]),
        published_at=published_at,
        stale_after=stale_after,
        baseline_used=baseline_used,
        primary_target=primary_target,
        alert_type=alert_type,
        model_status=model_status,
        metrics=ModelCardMetrics(
            brier_score=float(overall_metrics["brier_score"]),
            roc_auc=float(overall_metrics["roc_auc"]),
            precision_at_10=float(overall_metrics["precision"]),
            recall_at_5=None if alert_metrics.get("recall_at_5") is None else float(alert_metrics["recall_at_5"]),
            recall_at_10=None if alert_metrics.get("recall_at_10") is None else float(alert_metrics["recall_at_10"]),
            episode_recall=None
            if alert_metrics.get("episode_recall") is None
            else float(alert_metrics["episode_recall"]),
            false_alerts_per_true_alert=None
            if alert_metrics.get("false_alerts_per_true_alert") is None
            else float(alert_metrics["false_alerts_per_true_alert"]),
            no_clear_leader_rate=None
            if alert_metrics.get("no_clear_leader_rate") is None
            else float(alert_metrics["no_clear_leader_rate"]),
        ),
        threshold_policy=ThresholdPolicy(
            publish_top_n=publish_top_n,
            publish_threshold=None
            if alert_metrics.get("publish_threshold") is None
            else float(alert_metrics["publish_threshold"]),
            alert_threshold=float(alert_metrics.get("alert_threshold", alert_threshold)),
            warning_threshold=warning_threshold,
            operating_threshold=operating_threshold,
        ),
        provenance=provenance,
    )


def build_site_snapshot(
    *,
    run_name: str,
    preferred_prediction_file: Path,
    training_manifest_file: Path,
    training_metrics_file: Path,
    calibration_metrics_file: Path,
    backtest_metrics_file: Path,
    report_inputs_file: Path | None,
    output_dir: Path,
    secondary_prediction_file: Path | None = None,
    baseline_prediction_file: Path | None = None,
    secondary_training_manifest_file: Path | None = None,
    secondary_training_metrics_file: Path | None = None,
    secondary_calibration_metrics_file: Path | None = None,
    secondary_backtest_metrics_file: Path | None = None,
    structural_training_manifest_file: Path | None = None,
    structural_calibration_metrics_file: Path | None = None,
    structural_backtest_metrics_file: Path | None = None,
    baseline_training_manifest_file: Path | None = None,
    baseline_training_metrics_file: Path | None = None,
    baseline_calibration_metrics_file: Path | None = None,
    baseline_backtest_metrics_file: Path | None = None,
    published_at: str | datetime | None = None,
    fresh_window_days: int = 10,
    stale_window_days: int = 21,
    publish_top_n: int = 10,
    alert_threshold: float = 0.7,
    warning_threshold: float = 0.5,
    operating_threshold: float | None = 0.6,
) -> SiteSnapshotRunResult:
    config = SiteSnapshotConfig(
        run_name=run_name,
        preferred_prediction_file=preferred_prediction_file,
        secondary_prediction_file=secondary_prediction_file,
        baseline_prediction_file=baseline_prediction_file,
        training_manifest_file=training_manifest_file,
        training_metrics_file=training_metrics_file,
        calibration_metrics_file=calibration_metrics_file,
        backtest_metrics_file=backtest_metrics_file,
        secondary_training_manifest_file=secondary_training_manifest_file,
        secondary_training_metrics_file=secondary_training_metrics_file,
        secondary_calibration_metrics_file=secondary_calibration_metrics_file,
        secondary_backtest_metrics_file=secondary_backtest_metrics_file,
        structural_training_manifest_file=structural_training_manifest_file,
        structural_calibration_metrics_file=structural_calibration_metrics_file,
        structural_backtest_metrics_file=structural_backtest_metrics_file,
        baseline_training_manifest_file=baseline_training_manifest_file,
        baseline_training_metrics_file=baseline_training_metrics_file,
        baseline_calibration_metrics_file=baseline_calibration_metrics_file,
        baseline_backtest_metrics_file=baseline_backtest_metrics_file,
        report_inputs_file=report_inputs_file,
        output_dir=output_dir,
        published_at=None if published_at is None else _as_utc_datetime(published_at),
        fresh_window_days=fresh_window_days,
        stale_window_days=stale_window_days,
        publish_top_n=publish_top_n,
        alert_threshold=alert_threshold,
        warning_threshold=warning_threshold,
        operating_threshold=operating_threshold,
    )
    return build_site_snapshot_from_config(config)


def build_site_snapshot_from_config(config: SiteSnapshotConfig) -> SiteSnapshotRunResult:
    prediction_frame, prediction_file, baseline_used = _load_prediction_frame_with_fallback(config)
    (
        training_manifest_file,
        training_metrics_file,
        calibration_metrics_file,
        backtest_metrics_file,
    ) = _select_metadata_files(config, baseline_used=baseline_used)
    training_manifest = _load_json(training_manifest_file)
    training_metrics = _load_json(training_metrics_file)
    calibration_metrics = _load_json(calibration_metrics_file)
    backtest_metrics = _load_json(backtest_metrics_file)
    secondary_provenance = None
    secondary_target_name = None
    structural_provenance = None
    secondary_metadata_files = _secondary_metadata_files(config)
    if secondary_metadata_files is not None:
        (
            secondary_training_manifest_file,
            _secondary_training_metrics_file,
            secondary_calibration_metrics_file,
            secondary_backtest_metrics_file,
        ) = secondary_metadata_files
        secondary_training_manifest = _load_json(secondary_training_manifest_file)
        secondary_calibration_metrics = _load_json(secondary_calibration_metrics_file)
        secondary_backtest_metrics = _load_json(secondary_backtest_metrics_file)
        secondary_target_name = str(secondary_training_manifest["target_name"])
        secondary_provenance = _build_target_provenance(
            training_manifest_file=secondary_training_manifest_file,
            training_manifest=secondary_training_manifest,
            calibration_metrics_file=secondary_calibration_metrics_file,
            calibration_metrics=secondary_calibration_metrics,
            backtest_metrics_file=secondary_backtest_metrics_file,
            backtest_metrics=secondary_backtest_metrics,
        )
    structural_metadata_files = _structural_metadata_files(config)
    if structural_metadata_files is not None:
        (
            structural_training_manifest_file,
            structural_calibration_metrics_file,
            structural_backtest_metrics_file,
        ) = structural_metadata_files
        structural_training_manifest = _load_json(structural_training_manifest_file)
        structural_calibration_metrics = _load_json(structural_calibration_metrics_file)
        structural_backtest_metrics = _load_json(structural_backtest_metrics_file)
        structural_provenance = _build_target_provenance(
            training_manifest_file=structural_training_manifest_file,
            training_manifest=structural_training_manifest,
            calibration_metrics_file=structural_calibration_metrics_file,
            calibration_metrics=structural_calibration_metrics,
            backtest_metrics_file=structural_backtest_metrics_file,
            backtest_metrics=structural_backtest_metrics,
        )
    report_inputs = _load_report_inputs(config.report_inputs_file)

    snapshot_values = prediction_frame["snapshot_ts_utc"].dropna() if "snapshot_ts_utc" in prediction_frame.columns else pd.Series(dtype="datetime64[ns, UTC]")
    latest_snapshot_time = (
        snapshot_values.max().to_pydatetime().astimezone(UTC)
        if not snapshot_values.empty
        else prediction_frame["forecast_date"].max().to_pydatetime().replace(tzinfo=UTC)
    )
    published_at = config.published_at or latest_snapshot_time
    freshness_tier = _freshness_tier(
        reference_time=published_at,
        snapshot_time=latest_snapshot_time,
        fresh_window_days=config.fresh_window_days,
        stale_window_days=config.stale_window_days,
    )
    snapshots, _, forecast_as_of, lead_tie_count = _build_country_snapshots(prediction_frame, freshness_tier=freshness_tier)
    if not snapshots:
        raise ValueError("Prediction artifact did not yield any country snapshots.")

    selected_model_name = str(prediction_frame.iloc[-1]["model_name"])
    model_version = str(prediction_frame.iloc[-1]["model_version"])
    target_name = str(prediction_frame.iloc[-1]["target_name"])
    horizon_days = int(prediction_frame.iloc[-1]["horizon_days"])
    primary_target_provenance = _build_target_provenance(
        training_manifest_file=training_manifest_file,
        training_manifest=training_manifest,
        calibration_metrics_file=calibration_metrics_file,
        calibration_metrics=calibration_metrics,
        backtest_metrics_file=backtest_metrics_file,
        backtest_metrics=backtest_metrics,
    )
    provenance = _publication_provenance(
        primary_target_name=target_name,
        primary_target_provenance=primary_target_provenance,
        secondary_target_name=secondary_target_name,
        secondary_target_provenance=secondary_provenance,
        structural_target_provenance=structural_provenance,
    )
    fresh_until = published_at + timedelta(days=config.fresh_window_days)
    stale_after = published_at + timedelta(days=config.stale_window_days)
    top_model_name = backtest_metrics.get("comparison", {}).get("top_model", {}).get("model_name")
    primary_model_name = backtest_metrics.get("primary_model")
    publish_threshold = backtest_metrics.get("alerts", {}).get("publish_threshold")
    second_score = snapshots[1].score if len(snapshots) > 1 else None
    primary_target, alert_type, no_clear_leader = _resolve_publication_state(
        target_name=target_name,
        lead_score=snapshots[0].score,
        second_score=second_score,
        lead_tie_count=lead_tie_count,
        baseline_used=baseline_used,
        primary_model_name=None if primary_model_name is None else str(primary_model_name),
        top_model_name=None if top_model_name is None else str(top_model_name),
        publish_threshold=None if publish_threshold is None else float(publish_threshold),
    )
    model_status = "promoted" if alert_type not in {"Monitoring Only", "No Clear Leader"} else "monitoring_only"
    predicted_conflict = _build_predicted_conflict(
        snapshots,
        report_inputs,
        target_name=target_name,
        horizon_days=horizon_days,
    )
    forecast_snapshot = ForecastSnapshot(
        forecast_as_of=forecast_as_of,
        lead_country_iso3=snapshots[0].iso3,
        lead_country_name=snapshots[0].country_name,
        predicted_conflict=predicted_conflict,
        primary_target=primary_target,
        alert_type=alert_type,
        no_clear_leader=no_clear_leader,
        coverage_count=len(snapshots),
        countries=snapshots,
    )
    manifest = WebsiteSnapshotManifest(
        snapshot_id=f"{config.run_name}-{published_at.date().isoformat()}",
        published_at=published_at,
        fresh_until=fresh_until,
        stale_after=stale_after,
        baseline_used=baseline_used,
        forecast_as_of=forecast_as_of,
        generated_at=published_at,
        coverage_count=len(snapshots),
        top_country_iso3=snapshots[0].iso3,
        top_country_name=snapshots[0].country_name,
        predicted_conflict=predicted_conflict,
        primary_target=primary_target,
        alert_type=alert_type,
        model_status=model_status,
        no_clear_leader=no_clear_leader,
        provenance=provenance,
    )
    model_card = _build_model_card(
        selected_model_name=selected_model_name,
        model_version=model_version,
        training_manifest=training_manifest,
        training_metrics=training_metrics,
        backtest_metrics=backtest_metrics,
        provenance=provenance,
        published_at=published_at,
        stale_after=stale_after,
        baseline_used=baseline_used,
        primary_target=primary_target,
        alert_type=alert_type,
        model_status=model_status,
        publish_top_n=config.publish_top_n,
        alert_threshold=config.alert_threshold,
        warning_threshold=config.warning_threshold,
        operating_threshold=config.operating_threshold,
    )
    bundle = WebsiteSnapshotBundle(
        manifest=manifest,
        forecast_snapshot=forecast_snapshot,
        model_card=model_card,
    )
    country_payloads = _build_country_detail_payloads(
        snapshots,
        prediction_frame,
        report_inputs,
        model_name=selected_model_name,
        model_version=model_version,
        target_name=target_name,
        horizon_days=horizon_days,
    )
    backtest_summary = {
        "primary_model": backtest_metrics.get("primary_model"),
        "baseline_model": backtest_metrics.get("baseline_model"),
        "top_model_name": top_model_name,
        "primary_target": primary_target,
        "alert_type": alert_type,
        "model_status": model_status,
        "no_clear_leader": no_clear_leader,
        "publish_threshold": publish_threshold,
        "alert_threshold": backtest_metrics.get("alerts", {}).get("alert_threshold"),
        "episode_recall": backtest_metrics.get("alerts", {}).get("episode_recall"),
        "false_alerts_per_true_alert": backtest_metrics.get("alerts", {}).get("false_alerts_per_true_alert"),
        "recall_at_5": backtest_metrics.get("alerts", {}).get("recall_at_5"),
        "recall_at_10": backtest_metrics.get("alerts", {}).get("recall_at_10"),
        "no_clear_leader_rate": backtest_metrics.get("alerts", {}).get("no_clear_leader_rate"),
        "false_alert_burden": backtest_metrics.get("alerts", {}).get("false_alert_burden"),
        "new_alert_count": backtest_metrics.get("alerts", {}).get("new_alert_count"),
        "true_alert_count": backtest_metrics.get("alerts", {}).get("true_alert_count"),
        "false_alert_count": backtest_metrics.get("alerts", {}).get("false_alert_count"),
        "calibration_method": backtest_metrics.get("calibration", {}).get("method"),
        "baseline_deltas": backtest_metrics.get("comparison", {}).get("baseline_deltas", []),
    }
    status_payload = {
        "status": "baseline_fallback" if baseline_used else "ok",
        "freshness_tier": freshness_tier.value,
        "published_at": published_at.isoformat(),
        "forecast_as_of": forecast_as_of.isoformat(),
        "baseline_used": baseline_used,
        "coverage_count": len(snapshots),
        "predicted_conflict": predicted_conflict.model_dump(mode="json"),
        "primary_target": primary_target,
        "alert_type": alert_type,
        "model_status": model_status,
        "no_clear_leader": no_clear_leader,
        "publish_threshold": publish_threshold,
        "alert_threshold": backtest_metrics.get("alerts", {}).get("alert_threshold"),
        "lead_country_iso3": snapshots[0].iso3,
        "lead_country_name": snapshots[0].country_name,
        "prediction_file": str(prediction_file),
        "lead_tie_count": lead_tie_count,
    }

    output_dir = config.output_dir
    country_dir = output_dir / "countries"
    manifest_file = output_dir / "manifest.json"
    forecast_snapshot_file = output_dir / "forecast_snapshot.json"
    backtest_summary_file = output_dir / "backtest_summary.json"
    model_card_file = output_dir / "model_card.json"
    status_file = output_dir / "status.json"

    write_json(manifest_file, manifest.model_dump(mode="json"))
    write_json(forecast_snapshot_file, forecast_snapshot.model_dump(mode="json"))
    write_json(backtest_summary_file, backtest_summary)
    write_json(model_card_file, model_card.model_dump(mode="json"))
    write_json(status_file, status_payload)
    for slug, payload in country_payloads.items():
        write_json(country_dir / f"{slug}.json", payload)

    return SiteSnapshotRunResult(
        output_dir=output_dir,
        manifest_file=manifest_file,
        forecast_snapshot_file=forecast_snapshot_file,
        backtest_summary_file=backtest_summary_file,
        model_card_file=model_card_file,
        status_file=status_file,
        country_dir=country_dir,
    )
