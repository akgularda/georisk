from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any


def create_run_dir(output_root: Path, stage: str, run_name: str) -> Path:
    run_dir = output_root / stage / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_pickle(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(payload, handle)


def load_pickle(path: Path) -> Any:
    with path.open("rb") as handle:
        return pickle.load(handle)
