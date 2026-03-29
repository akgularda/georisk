from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.common.logging import get_logger
from src.forecasting.utils import project_root
from src.social_publishing.review_queue import build_review_queue, write_review_exports

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class DryRunResult:
    output_dir: Path
    review_queue_file: Path
    review_markdown_file: Path


def run_dry_run(*, input_file: Path, output_dir: Path) -> DryRunResult:
    social_inputs = pd.read_parquet(input_file)
    review_queue = build_review_queue(social_inputs)
    review_queue_file, review_markdown_file = write_review_exports(review_queue, output_dir)
    return DryRunResult(
        output_dir=output_dir,
        review_queue_file=review_queue_file,
        review_markdown_file=review_markdown_file,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a dry-run social publishing review bundle.")
    parser.add_argument(
        "--input-file",
        type=Path,
        default=project_root() / "data" / "gold" / "social_inputs" / "social_inputs.parquet",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root() / "artifacts" / "social_publishing" / "dry_run" / "latest",
    )
    arguments = parser.parse_args()
    result = run_dry_run(input_file=arguments.input_file, output_dir=arguments.output_dir)
    LOGGER.info("Social publishing dry-run bundle written to %s", result.output_dir)


if __name__ == "__main__":
    main()
