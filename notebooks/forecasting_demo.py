from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting.calibrate import run_calibration
from src.forecasting.explain import run_explanations
from src.forecasting.predict import run_prediction
from src.forecasting.train import run_training


def main() -> None:
    config_dir = PROJECT_ROOT / "configs" / "forecasting"

    train_result = run_training(config_dir / "train_country_day_30d.yaml")
    calibration_result = run_calibration(
        config_dir / "calibrate_country_day.yaml",
        training_run_dir=train_result.run_dir,
    )
    prediction_result = run_prediction(
        config_dir / "predict_country_day.yaml",
        training_run_dir=train_result.run_dir,
        calibration_run_dir=calibration_result.run_dir,
    )
    explanation_result = run_explanations(
        config_dir / "explain_country_day.yaml",
        training_run_dir=train_result.run_dir,
        prediction_file=prediction_result.prediction_file,
    )

    print(f"train: {train_result.run_dir}")
    print(f"calibration: {calibration_result.run_dir}")
    print(f"prediction: {prediction_result.prediction_file}")
    print(f"explanations: {explanation_result.global_explanations_file}")


if __name__ == "__main__":
    main()
