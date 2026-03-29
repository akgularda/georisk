from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve


def _write_svg(path: Path, body: str, *, width: int = 720, height: int = 300) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
            "<rect width='100%' height='100%' fill='#081018'/>"
            f"{body}</svg>"
        ),
        encoding="utf-8",
    )


def write_probability_distribution_svg(predictions: pd.DataFrame, path: Path) -> Path:
    values = predictions["calibrated_probability"].astype(float).clip(0.0, 1.0).to_numpy()
    counts, _ = np.histogram(values, bins=10, range=(0.0, 1.0))
    max_count = max(int(counts.max()), 1)
    bar_width = 52
    gap = 12
    body = ["<text x='24' y='28' fill='#dce7f5' font-size='16' font-family='Inter'>Probability distribution</text>"]
    for index, count in enumerate(counts):
        height = int((count / max_count) * 180)
        x = 32 + index * (bar_width + gap)
        y = 240 - height
        body.append(f"<rect x='{x}' y='{y}' width='{bar_width}' height='{height}' fill='#8f1111' opacity='0.88'/>")
        body.append(
            f"<text x='{x + 8}' y='264' fill='#7f90a8' font-size='11' font-family='Inter'>{index / 10:.1f}</text>"
        )
    _write_svg(path, "".join(body))
    return path


def write_precision_recall_svg(predictions: pd.DataFrame, path: Path) -> Path:
    y_true = predictions["label"].astype(int).to_numpy()
    y_prob = predictions["calibrated_probability"].astype(float).clip(0.0, 1.0).to_numpy()
    if len(np.unique(y_true)) < 2:
        body = (
            "<text x='24' y='28' fill='#dce7f5' font-size='16' font-family='Inter'>Precision / recall</text>"
            "<text x='24' y='68' fill='#7f90a8' font-size='13' font-family='Inter'>Only one class present in the evaluation window.</text>"
        )
        _write_svg(path, body)
        return path

    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    points: list[str] = []
    for current_precision, current_recall in zip(precision, recall, strict=False):
        x = 48 + float(current_recall) * 620
        y = 240 - float(current_precision) * 180
        points.append(f"{x:.1f},{y:.1f}")
    body = (
        "<text x='24' y='28' fill='#dce7f5' font-size='16' font-family='Inter'>Precision / recall</text>"
        "<line x1='48' y1='240' x2='668' y2='240' stroke='#213042'/>"
        "<line x1='48' y1='60' x2='48' y2='240' stroke='#213042'/>"
        f"<polyline fill='none' stroke='#f0b323' stroke-width='3' points='{' '.join(points)}'/>"
    )
    _write_svg(path, body)
    return path

