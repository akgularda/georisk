from __future__ import annotations

DEFAULT_HORIZONS_DAYS = (7, 30, 90)


def validate_horizon(horizon_days: int) -> int:
    if horizon_days not in DEFAULT_HORIZONS_DAYS:
        raise ValueError(f"Unsupported horizon: {horizon_days}")
    return horizon_days

