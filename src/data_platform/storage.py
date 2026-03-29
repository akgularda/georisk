from __future__ import annotations

from pathlib import Path


def ensure_layer_dir(storage_root: Path, layer: str, dataset_name: str) -> Path:
    path = storage_root / layer / dataset_name
    path.mkdir(parents=True, exist_ok=True)
    return path
