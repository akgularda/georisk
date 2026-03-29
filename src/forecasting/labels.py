from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from src.forecasting.schemas import LabelDefinition, LabelKind


def _first_positive_date(
    future_dates: Iterable[object],
    future_values: Iterable[float],
) -> object | None:
    for current_date, value in zip(future_dates, future_values, strict=False):
        if float(value) > 0.0:
            return current_date
    return None


def build_labels(
    frame: pd.DataFrame,
    definition: LabelDefinition,
    horizon_days: int,
    *,
    entity_id_column: str = "entity_id",
    date_column: str = "as_of_date",
) -> pd.DataFrame:
    if definition.source_event_column not in frame.columns:
        raise ValueError(f"Missing source column for labels: {definition.source_event_column}")

    working = frame.copy()
    working[date_column] = pd.to_datetime(working[date_column]).dt.date
    working = working.sort_values(by=[entity_id_column, date_column], kind="mergesort")

    rows: list[dict[str, object]] = []
    for entity_id, group in working.groupby(entity_id_column, sort=False):
        dates = list(group[date_column])
        values = list(group[definition.source_event_column].astype(float))

        for index, as_of_date in enumerate(dates):
            future_values = values[index + 1 : index + 1 + horizon_days]
            future_dates = dates[index + 1 : index + 1 + horizon_days]
            if len(future_values) < horizon_days:
                rows.append(
                    {
                        entity_id_column: entity_id,
                        date_column: as_of_date,
                        "label": None,
                        "next_event_date": None,
                        "lookback_sum": None,
                        "future_sum": None,
                    }
                )
                continue

            lookback_values = values[max(0, index - definition.lookback_days) : index]
            lookback_sum = float(sum(lookback_values))
            future_sum = float(sum(future_values))
            next_event_date = _first_positive_date(future_dates, future_values)

            if definition.kind is LabelKind.ONSET:
                quiet_threshold = definition.quiet_threshold if definition.quiet_threshold is not None else 0.0
                label_value = int(lookback_sum <= quiet_threshold and future_sum >= definition.forecast_threshold)
            elif definition.kind is LabelKind.ESCALATION:
                baseline = max(lookback_sum, definition.minimum_baseline)
                threshold = max(definition.forecast_threshold, baseline * definition.growth_multiplier)
                label_value = int(future_sum >= threshold)
            else:
                label_value = int(future_sum >= definition.forecast_threshold)

            rows.append(
                {
                    entity_id_column: entity_id,
                    date_column: as_of_date,
                    "label": label_value,
                    "next_event_date": next_event_date,
                    "lookback_sum": lookback_sum,
                    "future_sum": future_sum,
                }
            )

    return pd.DataFrame(rows)

