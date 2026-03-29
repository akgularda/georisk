from __future__ import annotations

import io
from pathlib import Path

import pandas as pd


def parse_idea_election_calendar_csv(payload: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(payload))


def load_idea_election_calendar(snapshot_file: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(snapshot_file))
