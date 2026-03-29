from __future__ import annotations

import pandas as pd
import pytest

from src.data_platform.serving.social_inputs import SOCIAL_INPUT_COLUMNS
from src.social_publishing.review_queue import build_review_queue, write_review_exports


def _gold_social_inputs_row(*, post_id: str, country_iso3: str, country_name: str, summary_line: str, headline: str, body: str, source_snapshot_hash: str) -> dict[str, object]:
    return {
        "post_id": post_id,
        "platform_name": "generic",
        "country_iso3": country_iso3,
        "country_name": country_name,
        "publish_date": "2026-03-29",
        "as_of_date": "2026-03-29",
        "forecast_target": "label_escalation_30d",
        "forecast_horizon_days": 30,
        "forecast_probability": 0.42,
        "score_delta": 0.1,
        "summary_line": summary_line,
        "top_drivers": '["ACLED events (28d): 9"]',
        "report_slug": f"{country_iso3.lower()}-latest",
        "headline": headline,
        "body": body,
        "call_to_action": "Read the latest country risk brief.",
        "destination_url": f"/countries/{country_iso3.lower()}-latest",
        "source_snapshot_hash": source_snapshot_hash,
        "snapshot_ts_utc": "2026-03-28T00:00:00Z",
    }


def test_build_review_queue_preserves_gold_social_inputs_and_adds_review_fields(tmp_path) -> None:
    social_inputs = pd.DataFrame(
        [
            _gold_social_inputs_row(
                post_id="post-usa-latest",
                country_iso3="USA",
                country_name="United States",
                summary_line="United States moved to high risk in the latest weekly snapshot.",
                headline="United States risk watch: high",
                body="United States moved to high risk in the latest weekly snapshot. Drivers: ACLED events (28d): 9.",
                source_snapshot_hash="abc123",
            ),
            _gold_social_inputs_row(
                post_id="post-fra-latest",
                country_iso3="FRA",
                country_name="France",
                summary_line="France remains low risk in the latest weekly snapshot.",
                headline="France risk watch: low",
                body="France remains low risk in the latest weekly snapshot. Drivers: ACLED events (28d): 1.",
                source_snapshot_hash="def456",
            ),
        ]
    )

    review_queue = build_review_queue(social_inputs)
    review_queue_file, review_markdown_file = write_review_exports(review_queue, tmp_path)

    assert list(review_queue["post_id"]) == ["post-fra-latest", "post-usa-latest"]
    assert {"review_status", "review_notes", "formatted_post", "character_count"}.issubset(review_queue.columns)
    assert review_queue_file.exists()
    assert review_markdown_file.exists()
    assert "France risk watch: low" in review_markdown_file.read_text(encoding="utf-8")


def test_build_review_queue_preserves_input_schema_when_social_inputs_are_empty() -> None:
    social_inputs = pd.DataFrame(columns=SOCIAL_INPUT_COLUMNS)

    review_queue = build_review_queue(social_inputs)

    assert list(review_queue.columns) == [*SOCIAL_INPUT_COLUMNS, "review_status", "review_notes", "formatted_post", "character_count"]
    assert review_queue.empty


def test_build_review_queue_rejects_frames_that_do_not_match_gold_social_inputs_contract() -> None:
    social_inputs = pd.DataFrame(
        [
            {
                "post_id": "post-usa-latest",
                "platform_name": "generic",
                "country_iso3": "USA",
                "country_name": "United States",
                "publish_date": "2026-03-29",
                "summary_line": "United States moved to high risk in the latest weekly snapshot.",
                "headline": "United States risk watch: high",
                "body": "United States moved to high risk in the latest weekly snapshot. Drivers: ACLED events (28d): 9.",
                "call_to_action": "Read the latest country risk brief.",
                "destination_url": "/countries/usa-latest",
                "source_snapshot_hash": "abc123",
            }
        ]
    )

    with pytest.raises(ValueError, match="gold_social_inputs"):
        build_review_queue(social_inputs)
