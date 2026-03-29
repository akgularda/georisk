from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.orchestration.pipeline import run_live_country_signals_pipeline


def test_live_country_signals_pipeline_from_real_snapshots(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[3]
    result = run_live_country_signals_pipeline(
        project_root / "configs" / "data_platform" / "pipeline_live_country_signals.yaml",
        output_root=tmp_path,
        use_test_snapshots=True,
    )

    assert result.raw_manifest_file.exists()
    assert result.validation_report_file.exists()
    assert result.gold_country_signals_file.exists()

    gold = pd.read_parquet(result.gold_country_signals_file)
    assert not gold.empty
    assert "country_id" in gold.columns
    assert "current_event_count" in gold.columns
    assert "current_document_count" in gold.columns

