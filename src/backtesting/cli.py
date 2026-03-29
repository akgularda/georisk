from __future__ import annotations

import argparse
from pathlib import Path

from src.common.logging import get_logger

from src.backtesting.engine import run_backtest, run_replay

LOGGER = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run forecasting backtests.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a backtest")
    run_parser.add_argument("--config", required=True, type=Path)
    run_parser.add_argument("--output-root", type=Path, default=None)

    replay_parser = subparsers.add_parser("replay", help="Replay a single entity timeline")
    replay_parser.add_argument("--config", required=True, type=Path)
    replay_parser.add_argument("--output-root", type=Path, default=None)

    arguments = parser.parse_args()
    if arguments.command == "run":
        result = run_backtest(arguments.config, output_root=arguments.output_root)
        LOGGER.info("Backtest artifacts written to %s", result.run_dir)
        return
    result = run_replay(arguments.config, output_root=arguments.output_root)
    LOGGER.info("Replay written to %s", result.replay_file)


if __name__ == "__main__":
    main()
