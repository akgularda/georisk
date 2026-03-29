from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


COUNTRIES = [
    ("eth", "Ethiopia", "east_africa", "high"),
    ("col", "Colombia", "latin_america", "medium"),
    ("ukr", "Ukraine", "eastern_europe", "high"),
]


def _add_burst(series: np.ndarray, start: int, values: list[int]) -> None:
    for index, value in enumerate(values):
        position = start + index
        if 0 <= position < len(series):
            series[position] += value


def build_fixture_frame() -> pd.DataFrame:
    start_date = date(2023, 1, 1)
    periods = 240
    rng = np.random.default_rng(7)
    rows: list[dict[str, object]] = []

    for entity_index, (entity_id, entity_name, region, fragility_bucket) in enumerate(COUNTRIES):
        organized_violence = np.zeros(periods, dtype=int)
        protests = np.zeros(periods, dtype=int)
        interstate = np.zeros(periods, dtype=int)
        displacement = np.zeros(periods, dtype=float)

        violence_bursts = [35 + entity_index * 5, 105 + entity_index * 5, 175 + entity_index * 5]
        protest_bursts = [20 + entity_index * 7, 90 + entity_index * 7, 160 + entity_index * 7]
        interstate_bursts = [70 + entity_index * 3, 145 + entity_index * 3]

        for burst_start in violence_bursts:
            _add_burst(organized_violence, burst_start, [0, 1, 1, 2, 2, 1])
            _add_burst(displacement, burst_start + 1, [20, 30, 40, 50, 60, 30])
        for burst_start in protest_bursts:
            _add_burst(protests, burst_start, [1, 2, 2, 3, 1])
        for burst_start in interstate_bursts:
            _add_burst(interstate, burst_start, [0, 1, 1, 0])

        structural_fragility_index = 0.35 + (0.15 * entity_index)
        climate_base = 0.25 + (0.08 * entity_index)
        for day_index in range(periods):
            current_date = start_date + timedelta(days=day_index)
            macro_stress = 0.4 + 0.2 * np.sin((day_index + entity_index * 11) / 18)
            shipping_disruption = 0.2 + 0.15 * np.cos((day_index + entity_index * 5) / 23)
            climate_stress = climate_base + 0.1 * np.sin(day_index / 29)
            neighbor_spillover = 0.1 + 0.25 * (organized_violence[max(0, day_index - 7) : day_index + 1].sum() > 2)
            missing_macro_flag = int(day_index % 47 == 0)
            news_volume = (
                organized_violence[max(0, day_index - 6) : day_index + 1].sum()
                + protests[max(0, day_index - 6) : day_index + 1].sum()
                + 2
            )
            news_tone = -0.15 * organized_violence[max(0, day_index - 6) : day_index + 1].sum() + 0.05 * rng.normal()

            rows.append(
                {
                    "entity_id": entity_id,
                    "entity_name": entity_name,
                    "region": region,
                    "fragility_bucket": fragility_bucket,
                    "as_of_date": current_date.isoformat(),
                    "organized_violence_events": int(organized_violence[day_index]),
                    "protest_events": int(protests[day_index]),
                    "interstate_tension_events": int(interstate[day_index]),
                    "humanitarian_displacement_flow": float(displacement[day_index] + (10 * max(macro_stress, 0.0))),
                    "news_volume_7d": float(news_volume),
                    "news_tone_7d": float(news_tone),
                    "macro_stress_index": float(macro_stress),
                    "shipping_disruption_index": float(shipping_disruption),
                    "climate_stress_index": float(climate_stress),
                    "neighbor_spillover_index": float(neighbor_spillover),
                    "structural_fragility_index": float(structural_fragility_index),
                    "missing_macro_flag": missing_macro_flag,
                }
            )

    frame = pd.DataFrame(rows).sort_values(by=["entity_id", "as_of_date"]).reset_index(drop=True)
    for column, new_column in [
        ("organized_violence_events", "lag_1d_organized_violence_events"),
        ("organized_violence_events", "lag_7d_organized_violence_events"),
        ("protest_events", "lag_7d_protest_events"),
        ("humanitarian_displacement_flow", "lag_7d_displacement_flow"),
    ]:
        lag_days = int(new_column.split("_")[1].replace("d", ""))
        frame[new_column] = frame.groupby("entity_id")[column].shift(lag_days).fillna(0.0)

    grouped = frame.groupby("entity_id")
    frame["rolling_14d_violence_mean"] = (
        grouped["organized_violence_events"].shift(1).rolling(14, min_periods=1).mean().reset_index(level=0, drop=True)
    ).fillna(0.0)
    frame["rolling_30d_violence_volatility"] = (
        grouped["organized_violence_events"].shift(1).rolling(30, min_periods=2).std().reset_index(level=0, drop=True)
    ).fillna(0.0)
    frame["delta_7d_vs_30d_violence"] = frame["lag_7d_organized_violence_events"] - frame["rolling_14d_violence_mean"]
    frame["zscore_30d_news_volume"] = (
        (
            grouped["news_volume_7d"].shift(1).rolling(30, min_periods=5).mean().reset_index(level=0, drop=True)
            - frame["news_volume_7d"]
        )
        * -1.0
    ).fillna(0.0)

    return frame


def main() -> None:
    fixture_frame = build_fixture_frame()
    output_path = Path(__file__).with_name("synthetic_country_day.csv")
    fixture_frame.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()

