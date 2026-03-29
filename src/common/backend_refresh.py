from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TextIO
from urllib.request import Request, urlopen

DEFAULT_REVALIDATE_URL = "http://localhost:3000/api/revalidate"


@dataclass(frozen=True)
class RefreshStep:
    label: str
    arguments: tuple[str, ...]
    max_attempts: int = 1
    retry_delay_seconds: float = 5.0


def build_refresh_steps(repo_root: Path) -> list[RefreshStep]:
    forecasting_root = repo_root / "artifacts" / "forecasting"
    baseline_training_run_dir = forecasting_root / "train" / "country_week_30d"
    baseline_calibration_run_dir = forecasting_root / "calibration" / "country_week_default"
    structural_training_run_dir = forecasting_root / "train" / "country_week_onset_structural_90d"
    structural_calibration_run_dir = forecasting_root / "calibration" / "country_week_onset_structural_90d"
    onset_training_run_dir = forecasting_root / "train" / "country_week_onset_logit_30d"
    onset_calibration_run_dir = forecasting_root / "calibration" / "country_week_onset_logit"
    interstate_structural_training_run_dir = forecasting_root / "train" / "country_week_interstate_onset_structural_90d"
    interstate_structural_calibration_run_dir = forecasting_root / "calibration" / "country_week_interstate_onset_structural_90d"
    interstate_onset_training_run_dir = forecasting_root / "train" / "country_week_interstate_onset_logit_30d"
    interstate_onset_calibration_run_dir = forecasting_root / "calibration" / "country_week_interstate_onset_logit"
    logit_training_run_dir = forecasting_root / "train" / "country_week_logit_30d"
    logit_calibration_run_dir = forecasting_root / "calibration" / "country_week_logit"

    return [
        RefreshStep(
            "Build dense country-week features",
            ("-m", "src.data_platform.orchestration.cli", "run", "--config", "configs/data_platform/pipeline_country_week_features.yaml"),
            max_attempts=3,
        ),
        RefreshStep(
            "Train baseline country-week model",
            ("-m", "src.forecasting.train", "--config", "configs/forecasting/train_country_week_30d.yaml"),
        ),
        RefreshStep(
            "Calibrate baseline country-week model",
            (
                "-m",
                "src.forecasting.calibrate",
                "--config",
                "configs/forecasting/calibrate_country_week.yaml",
                "--training-run-dir",
                str(baseline_training_run_dir),
            ),
        ),
        RefreshStep(
            "Predict baseline country-week model",
            (
                "-m",
                "src.forecasting.predict",
                "--config",
                "configs/forecasting/predict_country_week.yaml",
                "--training-run-dir",
                str(baseline_training_run_dir),
                "--calibration-run-dir",
                str(baseline_calibration_run_dir),
            ),
        ),
        RefreshStep(
            "Train structural onset country-week model",
            ("-m", "src.forecasting.train", "--config", "configs/forecasting/train_country_week_onset_structural_90d.yaml"),
        ),
        RefreshStep(
            "Calibrate structural onset country-week model",
            (
                "-m",
                "src.forecasting.calibrate",
                "--config",
                "configs/forecasting/calibrate_country_week_onset_structural_90d.yaml",
                "--training-run-dir",
                str(structural_training_run_dir),
            ),
        ),
        RefreshStep(
            "Predict structural onset country-week model",
            (
                "-m",
                "src.forecasting.predict",
                "--config",
                "configs/forecasting/predict_country_week_onset_structural_90d.yaml",
                "--training-run-dir",
                str(structural_training_run_dir),
                "--calibration-run-dir",
                str(structural_calibration_run_dir),
            ),
        ),
        RefreshStep(
            "Run structural onset backtest",
            ("-m", "src.backtesting.cli", "run", "--config", "configs/backtesting/country_week_onset_structural_90d.yaml"),
        ),
        RefreshStep(
            "Train onset country-week model",
            ("-m", "src.forecasting.train", "--config", "configs/forecasting/train_country_week_onset_logit_30d.yaml"),
        ),
        RefreshStep(
            "Calibrate onset country-week model",
            (
                "-m",
                "src.forecasting.calibrate",
                "--config",
                "configs/forecasting/calibrate_country_week_onset_logit.yaml",
                "--training-run-dir",
                str(onset_training_run_dir),
            ),
        ),
        RefreshStep(
            "Predict onset country-week model",
            (
                "-m",
                "src.forecasting.predict",
                "--config",
                "configs/forecasting/predict_country_week_onset_logit.yaml",
                "--training-run-dir",
                str(onset_training_run_dir),
                "--calibration-run-dir",
                str(onset_calibration_run_dir),
            ),
        ),
        RefreshStep(
            "Train interstate structural country-week model",
            ("-m", "src.forecasting.train", "--config", "configs/forecasting/train_country_week_interstate_onset_structural_90d.yaml"),
        ),
        RefreshStep(
            "Calibrate interstate structural country-week model",
            (
                "-m",
                "src.forecasting.calibrate",
                "--config",
                "configs/forecasting/calibrate_country_week_interstate_onset_structural_90d.yaml",
                "--training-run-dir",
                str(interstate_structural_training_run_dir),
            ),
        ),
        RefreshStep(
            "Predict interstate structural country-week model",
            (
                "-m",
                "src.forecasting.predict",
                "--config",
                "configs/forecasting/predict_country_week_interstate_onset_structural_90d.yaml",
                "--training-run-dir",
                str(interstate_structural_training_run_dir),
                "--calibration-run-dir",
                str(interstate_structural_calibration_run_dir),
            ),
        ),
        RefreshStep(
            "Run interstate structural backtest",
            ("-m", "src.backtesting.cli", "run", "--config", "configs/backtesting/country_week_interstate_onset_structural_90d.yaml"),
        ),
        RefreshStep(
            "Train interstate onset country-week model",
            ("-m", "src.forecasting.train", "--config", "configs/forecasting/train_country_week_interstate_onset_logit_30d.yaml"),
        ),
        RefreshStep(
            "Calibrate interstate onset country-week model",
            (
                "-m",
                "src.forecasting.calibrate",
                "--config",
                "configs/forecasting/calibrate_country_week_interstate_onset_logit.yaml",
                "--training-run-dir",
                str(interstate_onset_training_run_dir),
            ),
        ),
        RefreshStep(
            "Predict interstate onset country-week model",
            (
                "-m",
                "src.forecasting.predict",
                "--config",
                "configs/forecasting/predict_country_week_interstate_onset_logit.yaml",
                "--training-run-dir",
                str(interstate_onset_training_run_dir),
                "--calibration-run-dir",
                str(interstate_onset_calibration_run_dir),
            ),
        ),
        RefreshStep(
            "Run interstate onset backtest",
            ("-m", "src.backtesting.cli", "run", "--config", "configs/backtesting/country_week_interstate_onset_logit.yaml"),
        ),
        RefreshStep(
            "Train logit country-week model",
            ("-m", "src.forecasting.train", "--config", "configs/forecasting/train_country_week_logit_30d.yaml"),
        ),
        RefreshStep(
            "Calibrate logit country-week model",
            (
                "-m",
                "src.forecasting.calibrate",
                "--config",
                "configs/forecasting/calibrate_country_week_logit.yaml",
                "--training-run-dir",
                str(logit_training_run_dir),
            ),
        ),
        RefreshStep(
            "Predict logit country-week model",
            (
                "-m",
                "src.forecasting.predict",
                "--config",
                "configs/forecasting/predict_country_week_logit.yaml",
                "--training-run-dir",
                str(logit_training_run_dir),
                "--calibration-run-dir",
                str(logit_calibration_run_dir),
            ),
        ),
        RefreshStep(
            "Run onset backtest",
            ("-m", "src.backtesting.cli", "run", "--config", "configs/backtesting/country_week_onset_logit.yaml"),
        ),
        RefreshStep(
            "Run logit backtest",
            ("-m", "src.backtesting.cli", "run", "--config", "configs/backtesting/country_week_logit.yaml"),
        ),
        RefreshStep(
            "Publish website snapshot",
            ("-m", "src.website_publishing.cli", "--config", "configs/website_publishing/site_snapshot.yaml"),
        ),
    ]


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _log_line(log_handle: TextIO, message: str) -> None:
    line = f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] {message}"
    print(line)
    log_handle.write(f"{line}\n")
    log_handle.flush()


def _write_output(log_handle: TextIO, output: str) -> None:
    if not output:
        return
    text = output if output.endswith("\n") else f"{output}\n"
    print(text, end="")
    log_handle.write(text)
    log_handle.flush()


def _run_step(*, python_executable: str, step: RefreshStep, repo_root: Path, log_handle: TextIO) -> None:
    command = [python_executable, *step.arguments]
    for attempt in range(1, step.max_attempts + 1):
        _log_line(log_handle, step.label if step.max_attempts == 1 else f"{step.label} (attempt {attempt}/{step.max_attempts})")
        log_handle.write(f"{json.dumps(command)}\n")
        log_handle.flush()

        completed = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        _write_output(log_handle, completed.stdout)
        _write_output(log_handle, completed.stderr)
        if completed.returncode == 0:
            return
        if attempt == step.max_attempts:
            raise RuntimeError(f"Step failed: {step.label}")
        _log_line(log_handle, f"Attempt {attempt} of {step.max_attempts} failed for {step.label}; retrying in {step.retry_delay_seconds:g}s")
        time.sleep(step.retry_delay_seconds)


def _post_revalidate(url: str, log_handle: TextIO) -> None:
    request = Request(url, method="POST")
    with urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace").strip()
    if body:
        _write_output(log_handle, body)


def run_backend_refresh(
    *,
    repo_root: Path,
    python_executable: str | None = None,
    log_root: Path | None = None,
    revalidate_url: str | None = DEFAULT_REVALIDATE_URL,
) -> Path:
    resolved_repo_root = repo_root.resolve()
    resolved_python = python_executable or sys.executable
    resolved_log_root = (log_root or (resolved_repo_root / "artifacts" / "ops")).resolve()
    resolved_log_root.mkdir(parents=True, exist_ok=True)
    log_file = resolved_log_root / f"backend-refresh-{_timestamp()}.log"

    with log_file.open("w", encoding="utf-8") as log_handle:
        _log_line(log_handle, "Backend refresh started")
        for step in build_refresh_steps(resolved_repo_root):
            _run_step(
                python_executable=resolved_python,
                step=step,
                repo_root=resolved_repo_root,
                log_handle=log_handle,
            )

        if revalidate_url:
            try:
                _post_revalidate(revalidate_url, log_handle)
            except Exception as exc:  # pragma: no cover - exercised via tests with monkeypatch.
                _log_line(log_handle, f"Revalidate skipped: {exc}")

        _log_line(log_handle, "Backend refresh completed")

    print(f"Backend refresh completed. Log: {log_file}")
    return log_file


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the full GeoRisk backend refresh pipeline.")
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--log-root", type=Path)
    parser.add_argument("--revalidate-url", default=DEFAULT_REVALIDATE_URL)
    parser.add_argument("--skip-revalidate", action="store_true")
    args = parser.parse_args(argv)

    run_backend_refresh(
        repo_root=args.repo_root,
        python_executable=args.python_executable,
        log_root=args.log_root,
        revalidate_url=None if args.skip_revalidate else args.revalidate_url,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
