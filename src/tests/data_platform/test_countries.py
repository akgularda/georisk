from __future__ import annotations

import math

from src.data_platform.countries import normalize_country_name_to_iso3


def test_normalize_country_name_to_iso3_returns_none_for_nan() -> None:
    assert normalize_country_name_to_iso3(math.nan) is None
