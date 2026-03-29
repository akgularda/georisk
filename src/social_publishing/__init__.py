from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.social_publishing.formatter import format_candidate_post
from src.social_publishing.review_queue import build_review_queue, write_review_exports

if TYPE_CHECKING:
    from src.social_publishing.cli import DryRunResult, run_dry_run

__all__ = [
    "DryRunResult",
    "build_review_queue",
    "format_candidate_post",
    "run_dry_run",
    "write_review_exports",
]


def __getattr__(name: str) -> Any:
    if name in {"DryRunResult", "run_dry_run"}:
        from src.social_publishing.cli import DryRunResult, run_dry_run

        cli_exports = {
            "DryRunResult": DryRunResult,
            "run_dry_run": run_dry_run,
        }
        return cli_exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
