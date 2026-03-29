from __future__ import annotations

import io
from pathlib import Path

import pandas as pd


def parse_wgi_snapshot_csv(payload: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(payload))


def load_wgi_snapshot(snapshot_file: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(snapshot_file))
