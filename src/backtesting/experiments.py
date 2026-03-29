from __future__ import annotations

from src.backtesting.schemas import BacktestConfig


def build_experiment_manifest(config: BacktestConfig, *, windows: list[dict[str, object]], available_models: list[str]) -> dict[str, object]:
    return {
        "run_name": config.run_name,
        "target_name": config.target_name,
        "horizon_days": config.horizon_days,
        "dataset_path": str(config.dataset_path),
        "dataset_spec": config.dataset_spec.model_dump(mode="json"),
        "label_column": config.label_column,
        "prediction_threshold": config.prediction_threshold,
        "calibration_method": config.calibration_method,
        "structural_prior": None if config.structural_prior is None else config.structural_prior.model_dump(mode="json"),
        "models": [model.model_dump(mode="json") for model in config.models],
        "available_models": available_models,
        "windows": windows,
    }
