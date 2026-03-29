from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.forecasting.features import validate_feature_frame
from src.forecasting.labels import build_labels
from src.forecasting.schemas import DatasetSpec, LabelDefinition, SplitWindow, StructuralPriorSpec
from src.forecasting.utils import resolve_path


def load_feature_frame(dataset_path: Path, dataset_spec: DatasetSpec) -> pd.DataFrame:
    if dataset_path.suffix == ".parquet":
        frame = pd.read_parquet(dataset_path)
    else:
        frame = pd.read_csv(dataset_path)
    return validate_feature_frame(frame, dataset_spec)


def attach_structural_prior(
    frame: pd.DataFrame,
    dataset_spec: DatasetSpec,
    structural_prior: StructuralPriorSpec,
) -> tuple[pd.DataFrame, list[str]]:
    prior_path = resolve_path(structural_prior.prediction_file)
    if prior_path.suffix == ".parquet":
        prior_frame = pd.read_parquet(prior_path)
    else:
        prior_frame = pd.read_csv(prior_path)

    required_columns = {
        structural_prior.entity_id_column,
        structural_prior.date_column,
        structural_prior.score_column,
    }
    missing_columns = sorted(required_columns.difference(prior_frame.columns))
    if missing_columns:
        raise ValueError(f"Missing structural prior columns: {missing_columns}")

    normalized_prior = prior_frame[
        [
            structural_prior.entity_id_column,
            structural_prior.date_column,
            structural_prior.score_column,
        ]
    ].copy()
    normalized_prior = normalized_prior.rename(
        columns={
            structural_prior.entity_id_column: dataset_spec.entity_id_column,
            structural_prior.date_column: dataset_spec.date_column,
            structural_prior.score_column: structural_prior.feature_name,
        }
    )
    normalized_prior[dataset_spec.date_column] = pd.to_datetime(
        normalized_prior[dataset_spec.date_column],
        errors="coerce",
    ).dt.date
    normalized_prior = normalized_prior.dropna(
        subset=[dataset_spec.entity_id_column, dataset_spec.date_column]
    )

    if normalized_prior.duplicated([dataset_spec.entity_id_column, dataset_spec.date_column]).any():
        raise ValueError("Structural prior predictions must be unique by entity and forecast date.")

    augmented = frame.merge(
        normalized_prior,
        on=[dataset_spec.entity_id_column, dataset_spec.date_column],
        how="left",
        validate="many_to_one",
    )
    feature_columns = list(dataset_spec.feature_columns)
    if structural_prior.feature_name not in feature_columns:
        feature_columns.append(structural_prior.feature_name)
    return augmented, feature_columns


def prepare_training_frame(
    frame: pd.DataFrame,
    dataset_spec: DatasetSpec,
    label_definition: LabelDefinition,
    horizon_days: int,
) -> pd.DataFrame:
    labels = build_labels(
        frame[[dataset_spec.entity_id_column, dataset_spec.date_column, label_definition.source_event_column]],
        definition=label_definition,
        horizon_days=horizon_days,
        entity_id_column=dataset_spec.entity_id_column,
        date_column=dataset_spec.date_column,
    )
    merged = frame.merge(
        labels,
        on=[dataset_spec.entity_id_column, dataset_spec.date_column],
        how="left",
        validate="one_to_one",
    )
    labeled = merged.loc[merged["label"].notna()].copy()
    labeled["label"] = labeled["label"].astype(int)
    return labeled


def prepare_training_frame_from_precomputed_labels(
    frame: pd.DataFrame,
    dataset_spec: DatasetSpec,
    *,
    label_column: str,
    next_event_date_column: str | None = None,
) -> pd.DataFrame:
    if label_column not in frame.columns:
        raise ValueError(f"Missing precomputed label column: {label_column}")

    labeled = frame.loc[frame[label_column].notna()].copy()
    labeled["label"] = labeled[label_column].astype(int)
    if next_event_date_column:
        if next_event_date_column not in frame.columns:
            raise ValueError(f"Missing next-event column: {next_event_date_column}")
        labeled["next_event_date"] = pd.to_datetime(labeled[next_event_date_column], errors="coerce").dt.date
    else:
        labeled["next_event_date"] = pd.NaT
    return labeled


def summarize_label_distribution(frame: pd.DataFrame, *, label_column: str = "label") -> dict[str, int]:
    labels = frame.loc[frame[label_column].notna(), label_column].astype(int)
    positive_count = int((labels == 1).sum())
    negative_count = int((labels == 0).sum())
    return {
        "row_count": int(len(labels)),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "class_count": int(labels.nunique()),
    }


def build_walk_forward_splits(
    frame: pd.DataFrame,
    dataset_spec: DatasetSpec,
    *,
    min_train_periods: int,
    validation_window_periods: int,
    step_periods: int,
    max_splits: int | None = None,
) -> list[SplitWindow]:
    # Split widths are counted in observation periods at the dataset granularity.
    unique_dates = sorted(frame[dataset_spec.date_column].drop_duplicates())
    splits: list[SplitWindow] = []
    split_index = 0
    cursor = min_train_periods
    while cursor + validation_window_periods <= len(unique_dates):
        train_start = unique_dates[0]
        train_end = unique_dates[cursor - 1]
        validation_start = unique_dates[cursor]
        validation_end = unique_dates[cursor + validation_window_periods - 1]
        splits.append(
            SplitWindow(
                split_id=f"split_{split_index:02d}",
                train_start=train_start,
                train_end=train_end,
                validation_start=validation_start,
                validation_end=validation_end,
            )
        )
        split_index += 1
        if max_splits is not None and split_index >= max_splits:
            break
        cursor += step_periods
    return splits
