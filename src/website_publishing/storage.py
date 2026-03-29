from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Mapping, Protocol

from src.forecasting.utils import write_json
from src.website_publishing.schemas import FreshnessTier


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _publication_timestamp(value: datetime) -> str:
    return _normalize_datetime(value).strftime("%Y%m%dT%H%M%SZ")


def _safe_component(value: str) -> str:
    return value.replace("/", "-").replace("\\", "-").replace(":", "-").replace(" ", "_")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp-{uuid.uuid4().hex}")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)


def _atomic_write_json(path: Path, payload: Any) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, default=str))


def derive_freshness_tier(
    *,
    published_at: datetime,
    forecast_as_of: date,
    reference_time: datetime | None = None,
    fresh_window_days: int = 10,
    stale_window_days: int = 21,
    critical_window_days: int = 60,
) -> FreshnessTier:
    reference = _normalize_datetime(reference_time or published_at)
    lag_days = max((reference.date() - forecast_as_of).days, 0)
    if lag_days <= fresh_window_days:
        return FreshnessTier.FRESH
    if lag_days <= stale_window_days:
        return FreshnessTier.AGING
    if lag_days <= critical_window_days:
        return FreshnessTier.STALE
    return FreshnessTier.CRITICAL


@dataclass(frozen=True)
class WebsitePublicationBundle:
    snapshot_id: str
    published_at: datetime
    forecast_as_of: date
    manifest: Mapping[str, Any]
    forecast_snapshot: Mapping[str, Any]
    backtest_summary: Mapping[str, Any]
    model_card: Mapping[str, Any]
    status: Mapping[str, Any]
    countries: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class PublishedBundleLocation:
    bundle_dir: Path
    manifest_file: Path
    forecast_snapshot_file: Path
    backtest_summary_file: Path
    model_card_file: Path
    status_file: Path
    countries_dir: Path
    latest_manifest_pointer: Path


@dataclass(frozen=True)
class LatestManifestPointer:
    snapshot_id: str
    published_at: datetime
    forecast_as_of: date
    bundle_dir: Path
    manifest_path: Path


class WebsitePublicationStorage(Protocol):
    def publish(self, publication: WebsitePublicationBundle) -> PublishedBundleLocation:
        raise NotImplementedError

    def read_latest_pointer(self) -> LatestManifestPointer | None:
        raise NotImplementedError


class LocalFilesystemWebsitePublicationStorage:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir.resolve()
        self.bundles_dir = self.root_dir / "bundles"
        self.latest_manifest_pointer = self.root_dir / "latest_manifest.json"

    def publish(self, publication: WebsitePublicationBundle) -> PublishedBundleLocation:
        bundle_name = f"{_publication_timestamp(publication.published_at)}-{_safe_component(publication.snapshot_id)}"
        final_bundle_dir = self.bundles_dir / bundle_name
        if final_bundle_dir.exists():
            raise FileExistsError(f"Bundle directory already exists: {final_bundle_dir}")

        staging_dir = self.root_dir / ".staging" / f"{bundle_name}.{uuid.uuid4().hex}"
        self.bundles_dir.mkdir(parents=True, exist_ok=True)
        staging_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = staging_dir / "manifest.json"
        forecast_snapshot_file = staging_dir / "forecast_snapshot.json"
        backtest_summary_file = staging_dir / "backtest_summary.json"
        model_card_file = staging_dir / "model_card.json"
        status_file = staging_dir / "status.json"
        countries_dir = staging_dir / "countries"

        write_json(manifest_file, publication.manifest)
        write_json(forecast_snapshot_file, publication.forecast_snapshot)
        write_json(backtest_summary_file, publication.backtest_summary)
        write_json(model_card_file, publication.model_card)
        write_json(status_file, publication.status)
        for slug, payload in publication.countries.items():
            write_json(countries_dir / f"{slug}.json", payload)

        staging_dir.rename(final_bundle_dir)

        pointer_payload = {
            "snapshot_id": publication.snapshot_id,
            "published_at": _normalize_datetime(publication.published_at).isoformat(),
            "forecast_as_of": publication.forecast_as_of.isoformat(),
            "bundle_dir": final_bundle_dir.relative_to(self.root_dir).as_posix(),
            "manifest_path": (final_bundle_dir / "manifest.json").relative_to(self.root_dir).as_posix(),
        }
        _atomic_write_json(self.latest_manifest_pointer, pointer_payload)

        return PublishedBundleLocation(
            bundle_dir=final_bundle_dir,
            manifest_file=final_bundle_dir / "manifest.json",
            forecast_snapshot_file=final_bundle_dir / "forecast_snapshot.json",
            backtest_summary_file=final_bundle_dir / "backtest_summary.json",
            model_card_file=final_bundle_dir / "model_card.json",
            status_file=final_bundle_dir / "status.json",
            countries_dir=final_bundle_dir / "countries",
            latest_manifest_pointer=self.latest_manifest_pointer,
        )

    def read_latest_pointer(self) -> LatestManifestPointer | None:
        if not self.latest_manifest_pointer.exists():
            return None
        payload = json.loads(self.latest_manifest_pointer.read_text(encoding="utf-8"))
        return LatestManifestPointer(
            snapshot_id=str(payload["snapshot_id"]),
            published_at=datetime.fromisoformat(str(payload["published_at"])),
            forecast_as_of=date.fromisoformat(str(payload["forecast_as_of"])),
            bundle_dir=(self.root_dir / str(payload["bundle_dir"])).resolve(),
            manifest_path=(self.root_dir / str(payload["manifest_path"])).resolve(),
        )


__all__ = [
    "LatestManifestPointer",
    "LocalFilesystemWebsitePublicationStorage",
    "PublishedBundleLocation",
    "WebsitePublicationBundle",
    "WebsitePublicationStorage",
    "derive_freshness_tier",
]
