from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_platform.serving.social_inputs import SOCIAL_INPUT_COLUMNS
from src.social_publishing.formatter import format_candidate_post

REVIEW_QUEUE_FIELDS = [
    "review_status",
    "review_notes",
    "formatted_post",
    "character_count",
]


def _validate_social_inputs_contract(social_inputs: pd.DataFrame) -> None:
    missing_columns = [column for column in SOCIAL_INPUT_COLUMNS if column not in social_inputs.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            "social_inputs must match the gold_social_inputs contract; "
            f"missing columns: {missing}"
        )


def build_review_queue(social_inputs: pd.DataFrame) -> pd.DataFrame:
    _validate_social_inputs_contract(social_inputs)
    if social_inputs.empty:
        return pd.DataFrame(columns=[*social_inputs.columns, *REVIEW_QUEUE_FIELDS])

    formatted_rows = []
    for row in social_inputs.to_dict(orient="records"):
        formatted = format_candidate_post(row)
        formatted_rows.append({**row, **formatted})

    review_queue = pd.DataFrame.from_records(formatted_rows)
    sort_columns = [column for column in ["publish_date", "country_iso3", "post_id"] if column in review_queue.columns]
    if sort_columns:
        review_queue = review_queue.sort_values(sort_columns, kind="mergesort").reset_index(drop=True)
    return review_queue


def write_review_exports(review_queue: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    review_queue_file = output_dir / "review_queue.parquet"
    review_markdown_file = output_dir / "review_queue.md"
    review_queue.to_parquet(review_queue_file, index=False)

    lines = ["# Social Publishing Dry Run", ""]
    for row in review_queue.to_dict(orient="records"):
        lines.extend(
            [
                f"## {row['post_id']}",
                "",
                f"- Country: `{row['country_name']}`",
                f"- Platform: `{row['platform_name']}`",
                f"- Publish date: `{row['publish_date']}`",
                f"- Review status: `{row['review_status']}`",
                f"- Character count: `{row['character_count']}`",
                "",
                "### Candidate post",
                "",
                str(row["formatted_post"]),
                "",
            ]
        )

    review_markdown_file.write_text("\n".join(lines), encoding="utf-8")
    return review_queue_file, review_markdown_file
