from __future__ import annotations

from io import StringIO
from pathlib import Path
from urllib.error import URLError

import pytest

from src.common.backend_refresh import (
    DEFAULT_COUNTRY_WEEK_FEATURES_CONFIG,
    DEFAULT_REVALIDATE_URL,
    RefreshStep,
    _run_step,
    build_refresh_steps,
    run_backend_refresh,
)


def test_build_refresh_steps_covers_daily_pipeline(tmp_path: Path) -> None:
    steps = build_refresh_steps(tmp_path)

    labels = [step.label for step in steps]
    assert labels == [
        "Build dense country-week features",
        "Train baseline country-week model",
        "Calibrate baseline country-week model",
        "Predict baseline country-week model",
        "Train structural onset country-week model",
        "Calibrate structural onset country-week model",
        "Predict structural onset country-week model",
        "Run structural onset backtest",
        "Train onset country-week model",
        "Calibrate onset country-week model",
        "Predict onset country-week model",
        "Train interstate structural country-week model",
        "Calibrate interstate structural country-week model",
        "Predict interstate structural country-week model",
        "Run interstate structural backtest",
        "Train interstate onset country-week model",
        "Calibrate interstate onset country-week model",
        "Predict interstate onset country-week model",
        "Run interstate onset backtest",
        "Train logit country-week model",
        "Calibrate logit country-week model",
        "Predict logit country-week model",
        "Run onset backtest",
        "Run logit backtest",
        "Publish website snapshot",
    ]
    assert steps[0].arguments == (
        "-m",
        "src.data_platform.orchestration.cli",
        "run",
        "--config",
        DEFAULT_COUNTRY_WEEK_FEATURES_CONFIG,
    )
    assert steps[0].max_attempts == 3
    assert "--training-run-dir" in steps[2].arguments
    assert str(tmp_path / "artifacts" / "forecasting" / "train" / "country_week_30d") in steps[2].arguments
    assert "--calibration-run-dir" in steps[17].arguments
    assert str(tmp_path / "artifacts" / "forecasting" / "calibration" / "country_week_interstate_onset_logit") in steps[17].arguments
    assert all(step.max_attempts == 1 for step in steps[1:])
    assert steps[-1].arguments == (
        "-m",
        "src.website_publishing.cli",
        "--config",
        "configs/website_publishing/site_snapshot.yaml",
    )


def test_run_backend_refresh_executes_steps_writes_log_and_revalidates(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []
    revalidate_calls: list[str] = []

    def fake_run_step(*, python_executable: str, step, repo_root: Path, log_handle) -> None:
        calls.append((python_executable, *step.arguments))
        log_handle.write(f"completed {step.label}\n")

    def fake_post_revalidate(url: str, log_handle) -> None:
        revalidate_calls.append(url)
        log_handle.write("revalidated\n")

    monkeypatch.setattr("src.common.backend_refresh._run_step", fake_run_step)
    monkeypatch.setattr("src.common.backend_refresh._post_revalidate", fake_post_revalidate)

    log_file = run_backend_refresh(
        repo_root=tmp_path,
        python_executable="python-test",
    )

    assert log_file.parent == tmp_path / "artifacts" / "ops"
    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "Backend refresh started" in log_text
    assert "completed Build dense country-week features" in log_text
    assert "Backend refresh completed" in log_text
    assert len(calls) == 25
    assert calls[0][0] == "python-test"
    assert calls[-1] == (
        "python-test",
        "-m",
        "src.website_publishing.cli",
        "--config",
        "configs/website_publishing/site_snapshot.yaml",
    )
    assert revalidate_calls == [DEFAULT_REVALIDATE_URL]


def test_run_backend_refresh_supports_country_week_config_override(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run_step(*, python_executable: str, step, repo_root: Path, log_handle) -> None:
        calls.append((python_executable, *step.arguments))
        log_handle.write(f"completed {step.label}\n")

    monkeypatch.setattr("src.common.backend_refresh._run_step", fake_run_step)

    run_backend_refresh(
        repo_root=tmp_path,
        python_executable="python-test",
        revalidate_url=None,
        country_week_features_config="configs/data_platform/pipeline_country_week_features_daily.yaml",
    )

    assert calls[0] == (
        "python-test",
        "-m",
        "src.data_platform.orchestration.cli",
        "run",
        "--config",
        "configs/data_platform/pipeline_country_week_features_daily.yaml",
    )


def test_run_backend_refresh_logs_and_skips_failed_revalidate(tmp_path: Path, monkeypatch) -> None:
    def fake_run_step(*, python_executable: str, step, repo_root: Path, log_handle) -> None:
        log_handle.write(f"completed {step.label}\n")

    def failing_revalidate(url: str, log_handle) -> None:
        raise URLError("offline")

    monkeypatch.setattr("src.common.backend_refresh._run_step", fake_run_step)
    monkeypatch.setattr("src.common.backend_refresh._post_revalidate", failing_revalidate)

    log_file = run_backend_refresh(
        repo_root=tmp_path,
        python_executable="python-test",
        revalidate_url="http://localhost:3000/api/revalidate",
    )

    log_text = log_file.read_text(encoding="utf-8")
    assert "Revalidate skipped" in log_text
    assert "offline" in log_text


def test_run_backend_refresh_can_skip_revalidate_entirely(tmp_path: Path, monkeypatch) -> None:
    def fake_run_step(*, python_executable: str, step, repo_root: Path, log_handle) -> None:
        log_handle.write(f"completed {step.label}\n")

    def unexpected_revalidate(url: str, log_handle) -> None:
        raise AssertionError("revalidate should be skipped")

    monkeypatch.setattr("src.common.backend_refresh._run_step", fake_run_step)
    monkeypatch.setattr("src.common.backend_refresh._post_revalidate", unexpected_revalidate)

    log_file = run_backend_refresh(
        repo_root=tmp_path,
        python_executable="python-test",
        revalidate_url=None,
    )

    log_text = log_file.read_text(encoding="utf-8")
    assert "Revalidate skipped" not in log_text


def test_run_step_retries_retryable_steps_until_success(tmp_path: Path, monkeypatch) -> None:
    attempts = 0

    class FakePopen:
        def __init__(self, command, cwd, env, stdout, stderr, text, bufsize):
            nonlocal attempts
            attempts += 1
            self.stdout = StringIO("" if attempts == 1 else "ok\n")
            self._return_code = 1 if attempts == 1 else 0

        def wait(self) -> int:
            return self._return_code

    monkeypatch.setattr("src.common.backend_refresh.subprocess.Popen", FakePopen)
    monkeypatch.setattr("src.common.backend_refresh.time.sleep", lambda _: None)

    log_handle = StringIO()
    _run_step(
        python_executable="python-test",
        step=RefreshStep(
            "Build dense country-week features",
            ("-m", "src.data_platform.orchestration.cli", "run"),
            max_attempts=3,
        ),
        repo_root=tmp_path,
        log_handle=log_handle,
    )

    assert attempts == 2
    assert "Attempt 1 of 3 failed" in log_handle.getvalue()
    assert "ok" in log_handle.getvalue()


def test_run_step_raises_after_last_failed_attempt(tmp_path: Path, monkeypatch) -> None:
    class FakePopen:
        def __init__(self, command, cwd, env, stdout, stderr, text, bufsize):
            self.stdout = StringIO("still broken\n")
            self._return_code = 1

        def wait(self) -> int:
            return self._return_code

    monkeypatch.setattr("src.common.backend_refresh.subprocess.Popen", FakePopen)
    monkeypatch.setattr("src.common.backend_refresh.time.sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="Step failed: Publish website snapshot"):
        _run_step(
            python_executable="python-test",
            step=RefreshStep(
                "Publish website snapshot",
                ("-m", "src.website_publishing.cli", "--config", "configs/website_publishing/site_snapshot.yaml"),
                max_attempts=2,
            ),
            repo_root=tmp_path,
            log_handle=StringIO(),
        )
