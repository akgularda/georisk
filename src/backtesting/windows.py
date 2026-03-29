from __future__ import annotations

from src.forecasting.datasets import build_walk_forward_splits
from src.forecasting.schemas import DatasetSpec, SplitWindow


def build_backtest_windows(frame, dataset_spec: DatasetSpec, split_config) -> list[SplitWindow]:
    return build_walk_forward_splits(
        frame,
        dataset_spec,
        min_train_periods=split_config.min_train_periods,
        validation_window_periods=split_config.validation_window_periods,
        step_periods=split_config.step_periods,
        max_splits=split_config.max_splits,
    )
