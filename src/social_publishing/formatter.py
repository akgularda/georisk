from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_FORMATTER_FIELDS = [
    "post_id",
    "platform_name",
    "country_iso3",
    "country_name",
    "publish_date",
    "summary_line",
    "headline",
    "body",
    "call_to_action",
    "destination_url",
    "source_snapshot_hash",
]


def _validate_required_fields(record: Mapping[str, Any]) -> None:
    missing_fields = [field for field in REQUIRED_FORMATTER_FIELDS if field not in record]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"Social publishing record is missing required field(s): {missing}")


def _string_value(record: Mapping[str, Any], key: str) -> str:
    value = record.get(key)
    return "" if value is None else str(value)


def format_candidate_post(record: Mapping[str, Any]) -> dict[str, Any]:
    _validate_required_fields(record)
    headline = _string_value(record, "headline")
    body = _string_value(record, "body")
    call_to_action = _string_value(record, "call_to_action")
    destination_url = _string_value(record, "destination_url")
    call_to_action_line = call_to_action if not destination_url else f"{call_to_action} {destination_url}".strip()
    formatted_post = "\n\n".join(part for part in [headline, body, call_to_action_line] if part).strip()

    return {
        "post_id": _string_value(record, "post_id"),
        "platform_name": _string_value(record, "platform_name"),
        "country_iso3": _string_value(record, "country_iso3"),
        "country_name": _string_value(record, "country_name"),
        "publish_date": _string_value(record, "publish_date"),
        "summary_line": _string_value(record, "summary_line"),
        "headline": headline,
        "body": body,
        "call_to_action": call_to_action,
        "destination_url": destination_url,
        "source_snapshot_hash": _string_value(record, "source_snapshot_hash"),
        "review_status": "pending_review",
        "review_notes": "",
        "formatted_post": formatted_post,
        "character_count": len(formatted_post),
    }
