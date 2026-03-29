from __future__ import annotations

from pathlib import Path

from src.forecasting.registry import create_run_dir
from src.forecasting.utils import project_root


def default_output_root() -> Path:
    return project_root() / "artifacts" / "backtesting"


def resolve_backtest_run_dir(run_name: str, *, output_root: Path | None = None) -> Path:
    root = output_root or default_output_root()
    return create_run_dir(root, "run", run_name)


def resolve_replay_run_dir(run_name: str, *, output_root: Path | None = None) -> Path:
    root = output_root or default_output_root()
    return create_run_dir(root, "replay", run_name)
