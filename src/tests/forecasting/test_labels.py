from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.forecasting.datasets import prepare_training_frame_from_precomputed_labels
from src.forecasting.labels import build_labels
from src.forecasting.schemas import DatasetSpec, UnitOfAnalysis
from src.forecasting.schemas import LabelDefinition, LabelKind


def test_onset_labels_require_quiet_lookback_and_future_threshold() -> None:
    frame = pd.DataFrame(
        {
            "entity_id": ["eth"] * 8,
            "as_of_date": [date(2024, 1, 1) + timedelta(days=offset) for offset in range(8)],
            "organized_violence_events": [0, 0, 0, 0, 1, 1, 0, 0],
        }
    )

    definition = LabelDefinition(
        name="organized_violence_onset",
        kind=LabelKind.ONSET,
        source_event_column="organized_violence_events",
        lookback_days=3,
        forecast_threshold=2.0,
        quiet_threshold=0.0,
    )

    labeled = build_labels(frame, definition=definition, horizon_days=3)

    positive_row = labeled.loc[labeled["as_of_date"] == date(2024, 1, 3)].iloc[0]
    negative_row = labeled.loc[labeled["as_of_date"] == date(2024, 1, 5)].iloc[0]

    assert int(positive_row["label"]) == 1
    assert positive_row["next_event_date"] == date(2024, 1, 5)
    assert int(negative_row["label"]) == 0


def test_escalation_labels_require_growth_over_lookback() -> None:
    frame = pd.DataFrame(
        {
            "entity_id": ["col"] * 8,
            "as_of_date": [date(2024, 2, 1) + timedelta(days=offset) for offset in range(8)],
            "organized_violence_events": [1, 1, 1, 1, 3, 2, 0, 0],
        }
    )

    definition = LabelDefinition(
        name="organized_violence_escalation",
        kind=LabelKind.ESCALATION,
        source_event_column="organized_violence_events",
        lookback_days=3,
        forecast_threshold=4.0,
        growth_multiplier=1.5,
    )

    labeled = build_labels(frame, definition=definition, horizon_days=3)
    positive_row = labeled.loc[labeled["as_of_date"] == date(2024, 2, 2)].iloc[0]

    assert int(positive_row["label"]) == 1
    assert positive_row["next_event_date"] == date(2024, 2, 3)


def test_precomputed_labels_can_be_used_directly() -> None:
    frame = pd.DataFrame(
        {
            "country_iso3": ["IRN", "IRN", "ISR"],
            "week_start_date": [date(2026, 3, 2), date(2026, 3, 9), date(2026, 3, 2)],
            "signal_a": [1.0, 2.0, 3.0],
            "label_escalation_30d": [0, 1, None],
        }
    )
    dataset_spec = DatasetSpec(
        entity_id_column="country_iso3",
        entity_name_column="country_iso3",
        date_column="week_start_date",
        unit_of_analysis=UnitOfAnalysis.COUNTRY_WEEK,
        feature_columns=["signal_a"],
    )

    labeled = prepare_training_frame_from_precomputed_labels(
        frame,
        dataset_spec,
        label_column="label_escalation_30d",
    )

    assert len(labeled) == 2
    assert labeled["label"].tolist() == [0, 1]
    assert labeled["next_event_date"].isna().all()
