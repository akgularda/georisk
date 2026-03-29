from __future__ import annotations

from typing import Any

import pandas as pd


def summarize_table(table_name: str, frame: pd.DataFrame, *, key_columns: list[str]) -> dict[str, Any]:
    null_counts = {column: int(frame[column].isna().sum()) for column in key_columns if column in frame.columns}
    return {
        "table_name": table_name,
        "row_count": int(len(frame)),
        "columns": list(frame.columns),
        "null_counts": null_counts,
    }
