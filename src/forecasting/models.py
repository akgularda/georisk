from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin


@dataclass
class PriorRateModel(BaseEstimator, ClassifierMixin):
    probability_: float = 0.5
    classes_: np.ndarray | None = None

    def fit(self, x_frame: pd.DataFrame, y_series: pd.Series) -> "PriorRateModel":
        self.probability_ = float(y_series.mean())
        self.classes_ = np.asarray([0, 1], dtype=int)
        return self

    def predict_proba(self, x_frame: pd.DataFrame) -> np.ndarray:
        probabilities = np.full(shape=(len(x_frame),), fill_value=self.probability_, dtype=float)
        return np.column_stack([1.0 - probabilities, probabilities])
