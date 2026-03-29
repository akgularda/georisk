from __future__ import annotations

import io
from pathlib import Path

import pandas as pd


def parse_acled_csv(payload: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(payload))


def load_acled_snapshot(snapshot_file: str | Path) -> pd.DataFrame:
    path = Path(snapshot_file)
    return pd.read_csv(path)
