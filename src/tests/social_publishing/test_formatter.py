from __future__ import annotations

import pytest

from src.social_publishing.formatter import format_candidate_post


def test_format_candidate_post_builds_review_copy_from_gold_social_inputs_row() -> None:
    candidate = format_candidate_post(
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
    )

    assert candidate["post_id"] == "post-usa-latest"
    assert candidate["review_status"] == "pending_review"
    assert candidate["formatted_post"].startswith("United States risk watch: high\n\n")
    assert "\n\nRead the latest country risk brief. /countries/usa-latest" in candidate["formatted_post"]
    assert "Read the latest country risk brief." in candidate["formatted_post"]
    assert candidate["character_count"] == len(candidate["formatted_post"])
    assert candidate["source_snapshot_hash"] == "abc123"


def test_format_candidate_post_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="headline"):
        format_candidate_post(
            {
                "post_id": "post-usa-latest",
                "platform_name": "generic",
                "country_iso3": "USA",
                "country_name": "United States",
                "publish_date": "2026-03-29",
                "summary_line": "United States moved to high risk in the latest weekly snapshot.",
                "body": "United States moved to high risk in the latest weekly snapshot. Drivers: ACLED events (28d): 9.",
                "call_to_action": "Read the latest country risk brief.",
                "destination_url": "/countries/usa-latest",
                "source_snapshot_hash": "abc123",
            }
        )
