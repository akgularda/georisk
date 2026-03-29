from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from src.common.logging import get_logger
from src.data_platform.orchestration.pipeline import run_country_week_features_pipeline, run_live_country_signals_pipeline

LOGGER = get_logger(__name__)


def _load_pipeline_kind(config_path: Path) -> str:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return raw.get("pipeline_kind", "live_country_signals")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run data-platform pipelines.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", required=True, type=Path)
    run_parser.add_argument("--output-root", type=Path, default=None)
    run_parser.add_argument("--use-test-snapshots", action="store_true")

    arguments = parser.parse_args()
    if arguments.command == "run":
        pipeline_kind = _load_pipeline_kind(arguments.config)
        if pipeline_kind == "country_week_features":
            result = run_country_week_features_pipeline(
                arguments.config,
                output_root=arguments.output_root,
                use_test_snapshots=arguments.use_test_snapshots,
            )
            LOGGER.info("Gold country-week features written to %s", result.gold_country_week_features_file)
        else:
            result = run_live_country_signals_pipeline(
                arguments.config,
                output_root=arguments.output_root,
                use_test_snapshots=arguments.use_test_snapshots,
            )
            LOGGER.info("Gold country signals written to %s", result.gold_country_signals_file)


if __name__ == "__main__":
    main()
