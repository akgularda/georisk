from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from src.common.logging import get_logger
from src.forecasting.utils import resolve_path
from src.website_publishing.builder import SiteSnapshotRunResult, build_site_snapshot_from_config
from src.website_publishing.schemas import SiteSnapshotConfig

LOGGER = get_logger(__name__)


def _load_config(config_path: Path) -> SiteSnapshotConfig:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config_base_path = config_path.parents[2]
    path_fields = [
        "preferred_prediction_file",
        "baseline_prediction_file",
        "training_manifest_file",
        "training_metrics_file",
        "calibration_metrics_file",
        "backtest_metrics_file",
        "baseline_training_manifest_file",
        "baseline_training_metrics_file",
        "baseline_calibration_metrics_file",
        "baseline_backtest_metrics_file",
        "report_inputs_file",
        "output_dir",
    ]
    for field_name in path_fields:
        if raw.get(field_name):
            raw[field_name] = resolve_path(raw[field_name], config_base_path)
    return SiteSnapshotConfig.model_validate(raw)


def run_publish(*, config_path: Path) -> SiteSnapshotRunResult:
    config = _load_config(config_path)
    return build_site_snapshot_from_config(config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a canonical website snapshot bundle.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs") / "website_publishing" / "site_snapshot.yaml",
    )
    arguments = parser.parse_args()
    result = run_publish(config_path=arguments.config)
    LOGGER.info("Website snapshot bundle written to %s", result.output_dir)


if __name__ == "__main__":
    main()
