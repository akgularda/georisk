from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.social_publishing.cli import run_dry_run


def _gold_social_inputs_row() -> dict[str, object]:
    return {
        "post_id": "post-usa-latest",
        "platform_name": "generic",
        "country_iso3": "USA",
        "country_name": "United States",
        "publish_date": "2026-03-29",
        "as_of_date": "2026-03-29",
        "forecast_target": "label_escalation_30d",
        "forecast_horizon_days": 30,
        "forecast_probability": 0.42,
        "score_delta": 0.1,
        "summary_line": "United States moved to high risk in the latest weekly snapshot.",
        "top_drivers": '["ACLED events (28d): 9"]',
        "report_slug": "usa-latest",
        "headline": "United States risk watch: high",
        "body": "United States moved to high risk in the latest weekly snapshot. Drivers: ACLED events (28d): 9.",
        "call_to_action": "Read the latest country risk brief.",
        "destination_url": "/countries/usa-latest",
        "source_snapshot_hash": "abc123",
        "snapshot_ts_utc": "2026-03-28T00:00:00Z",
    }


def test_run_dry_run_reads_gold_social_inputs_and_writes_review_bundle(tmp_path) -> None:
    input_file = tmp_path / "social_inputs.parquet"
    pd.DataFrame([_gold_social_inputs_row()]).to_parquet(input_file, index=False)

    result = run_dry_run(input_file=input_file, output_dir=tmp_path / "dry_run")

    assert result.review_queue_file.exists()
    assert result.review_markdown_file.exists()
    assert result.review_queue_file.suffix == ".parquet"
    assert "United States risk watch: high" in result.review_markdown_file.read_text(encoding="utf-8")


def test_run_dry_run_rejects_non_contract_input(tmp_path) -> None:
    input_file = tmp_path / "social_inputs.parquet"
    pd.DataFrame(
        [
            {
                "post_id": "post-usa-latest",
                "platform_name": "generic",
                "country_iso3": "USA",
                "country_name": "United States",
                "publish_date": "2026-03-29",
            }
        ]
    ).to_parquet(input_file, index=False)

    with pytest.raises(ValueError, match="gold_social_inputs"):
        run_dry_run(input_file=input_file, output_dir=tmp_path / "dry_run")


def test_module_cli_runs_without_runpy_warning(tmp_path) -> None:
    input_file = tmp_path / "social_inputs.parquet"
    output_dir = tmp_path / "dry_run"
    pd.DataFrame([_gold_social_inputs_row()]).to_parquet(input_file, index=False)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.social_publishing.cli",
            "--input-file",
            str(input_file),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        cwd=Path(__file__).resolve().parents[3],
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "RuntimeWarning" not in completed.stderr
