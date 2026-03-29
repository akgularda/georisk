from __future__ import annotations

import pandas as pd


def normalize_unhcr_origin_population(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized = normalized.loc[normalized["coo_iso"].notna() & (normalized["coo_iso"] != "-")].copy()
    numeric_columns = [
        "refugees",
        "asylum_seekers",
        "returned_refugees",
        "idps",
        "returned_idps",
        "stateless",
        "ooc",
        "hst",
    ]
    for column in numeric_columns:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0)
    normalized["country_id"] = normalized["coo_iso"]
    return normalized[
        [
            "year",
            "country_id",
            "coo_name",
            "refugees",
            "asylum_seekers",
            "returned_refugees",
            "idps",
            "returned_idps",
            "stateless",
            "ooc",
            "hst",
        ]
    ].rename(columns={"coo_name": "country_name"})
