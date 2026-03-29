from __future__ import annotations

import pandas as pd

from src.forecasting.schemas import DatasetSpec


def validate_feature_frame(frame: pd.DataFrame, dataset_spec: DatasetSpec) -> pd.DataFrame:
    required_columns = {
        dataset_spec.entity_id_column,
        dataset_spec.entity_name_column,
        dataset_spec.date_column,
        *dataset_spec.feature_columns,
        *dataset_spec.group_columns,
    }
    missing_columns = sorted(required_columns.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"Missing required feature columns: {missing_columns}")

    validated = frame.copy()
    validated[dataset_spec.date_column] = pd.to_datetime(validated[dataset_spec.date_column]).dt.date
    return validated.sort_values(
        by=[dataset_spec.entity_id_column, dataset_spec.date_column],
        kind="mergesort",
    ).reset_index(drop=True)

