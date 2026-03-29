from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from src.website_publishing.storage import (
    LocalFilesystemWebsitePublicationStorage,
    WebsitePublicationBundle,
    derive_freshness_tier,
)


def _publication(
    *,
    snapshot_id: str,
    published_at: datetime,
    forecast_as_of: date,
    country_iso3: str,
    country_name: str,
    score: float,
) -> WebsitePublicationBundle:
    return WebsitePublicationBundle(
        snapshot_id=snapshot_id,
        published_at=published_at,
        forecast_as_of=forecast_as_of,
        manifest={
            "schema_version": "1.0.0",
            "snapshot_id": snapshot_id,
            "published_at": published_at.isoformat(),
            "forecast_as_of": forecast_as_of.isoformat(),
            "top_country_iso3": country_iso3,
            "top_country_name": country_name,
        },
        forecast_snapshot={
            "forecast_as_of": forecast_as_of.isoformat(),
            "lead_country_iso3": country_iso3,
            "lead_country_name": country_name,
            "coverage_count": 1,
            "countries": [
                {
                    "iso3": country_iso3,
                    "country_name": country_name,
                    "score": score,
                    "delta": 0.0,
                    "forecast_as_of": forecast_as_of.isoformat(),
                    "freshness_tier": "fresh",
                    "rank": 1,
                }
            ],
        },
        backtest_summary={"primary_model": "logit", "baseline_model": "prior_rate"},
        model_card={
            "model_name": "logit",
            "model_version": "country_week_logit_30d",
            "target_name": "country_week_escalation_30d",
        },
        status={
            "status": "ok",
            "freshness_tier": "fresh",
            "published_at": published_at.isoformat(),
            "forecast_as_of": forecast_as_of.isoformat(),
            "baseline_used": False,
            "coverage_count": 1,
            "lead_country_iso3": country_iso3,
            "lead_country_name": country_name,
        },
        countries={
            country_iso3.lower(): {
                "iso3": country_iso3,
                "country_name": country_name,
                "forecast": {
                    "score": score,
                    "delta": 0.0,
                    "rank": 1,
                    "forecast_as_of": forecast_as_of.isoformat(),
                    "freshness_tier": "fresh",
                },
            }
        },
    )


def test_derive_freshness_tier_uses_publication_and_forecast_dates() -> None:
    published_at = datetime(2026, 3, 28, 12, tzinfo=UTC)

    assert derive_freshness_tier(published_at=published_at, forecast_as_of=date(2026, 3, 27)) == "fresh"
    assert derive_freshness_tier(published_at=published_at, forecast_as_of=date(2026, 3, 14)) == "aging"
    assert derive_freshness_tier(published_at=published_at, forecast_as_of=date(2026, 2, 15)) == "stale"
    assert derive_freshness_tier(published_at=published_at, forecast_as_of=date(2025, 12, 1)) == "critical"


def test_local_storage_publishes_immutable_bundle_and_latest_pointer(tmp_path: Path) -> None:
    storage = LocalFilesystemWebsitePublicationStorage(tmp_path)

    first = storage.publish(
        _publication(
            snapshot_id="site_snapshot-2026-03-28",
            published_at=datetime(2026, 3, 28, 12, tzinfo=UTC),
            forecast_as_of=date(2026, 3, 23),
            country_iso3="LBN",
            country_name="Lebanon",
            score=0.84,
        )
    )
    second = storage.publish(
        _publication(
            snapshot_id="site_snapshot-2026-03-29",
            published_at=datetime(2026, 3, 29, 12, tzinfo=UTC),
            forecast_as_of=date(2026, 3, 24),
            country_iso3="ISR",
            country_name="Israel",
            score=0.91,
        )
    )

    assert first.bundle_dir.exists()
    assert second.bundle_dir.exists()
    assert first.bundle_dir != second.bundle_dir
    assert (first.bundle_dir / "manifest.json").exists()
    assert (first.bundle_dir / "countries" / "lbn.json").exists()
    assert (second.bundle_dir / "countries" / "isr.json").exists()

    pointer_payload = json.loads(storage.latest_manifest_pointer.read_text(encoding="utf-8"))
    assert pointer_payload["snapshot_id"] == "site_snapshot-2026-03-29"
    assert pointer_payload["bundle_dir"] == second.bundle_dir.relative_to(tmp_path).as_posix()
    assert pointer_payload["manifest_path"] == second.manifest_file.relative_to(tmp_path).as_posix()

    latest = storage.read_latest_pointer()
    assert latest is not None
    assert latest.bundle_dir == second.bundle_dir
    assert latest.manifest_path == second.manifest_file
    assert latest.snapshot_id == "site_snapshot-2026-03-29"

    first_manifest = (first.bundle_dir / "manifest.json").read_text(encoding="utf-8")
    second_manifest = (second.bundle_dir / "manifest.json").read_text(encoding="utf-8")
    assert "LBN" in first_manifest
    assert "ISR" in second_manifest
