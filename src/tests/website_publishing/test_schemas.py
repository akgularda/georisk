from __future__ import annotations

import json
from pathlib import Path

from src.website_publishing.schemas import (
    ForecastSnapshot,
    FreshnessTier,
    ModelCardMetrics,
    ModelCardPayload,
    WebsiteSnapshotBundle,
    WebsiteSnapshotManifest,
)


ROOT = Path(__file__).resolve().parents[3]
CONTRACT_DIR = ROOT / "contracts"
EXAMPLE_PATH = ROOT / "artifacts" / "examples" / "website_snapshot_example.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_snapshot_contract_declares_canonical_manifest_and_country_entries() -> None:
    schema = _load_json(CONTRACT_DIR / "website_snapshot.schema.json")

    assert schema["type"] == "object"
    assert set(schema["required"]) == {"manifest", "forecast_snapshot", "model_card"}

    manifest_schema = schema["properties"]["manifest"]
    assert set(manifest_schema["required"]) >= {
        "published_at",
        "stale_after",
        "baseline_used",
        "primary_target",
        "alert_type",
        "model_status",
        "no_clear_leader",
        "predicted_conflict",
        "provenance",
    }
    assert set(manifest_schema["properties"]["provenance"]["required"]) == {
        "onset",
        "escalation",
        "structural",
    }

    forecast_schema = schema["properties"]["forecast_snapshot"]
    assert set(forecast_schema["required"]) >= {"primary_target", "alert_type", "no_clear_leader", "predicted_conflict"}
    country_schema = forecast_schema["properties"]["countries"]["items"]
    assert set(country_schema["required"]) >= {
        "iso3",
        "country_name",
        "score",
        "delta",
        "forecast_as_of",
        "freshness_tier",
    }
    predicted_conflict_schema = schema["$defs"]["predicted_conflict"]
    assert set(predicted_conflict_schema["required"]) >= {
        "label",
        "countries",
        "reason_source",
    }


def test_model_card_contract_declares_metrics_and_threshold_policy() -> None:
    schema = _load_json(CONTRACT_DIR / "model_card.schema.json")

    assert schema["type"] == "object"
    assert set(schema["required"]) >= {
        "model_name",
        "published_at",
        "stale_after",
        "baseline_used",
        "primary_target",
        "alert_type",
        "model_status",
        "metrics",
        "threshold_policy",
        "provenance",
    }
    assert set(schema["properties"]["metrics"]["required"]) >= {
        "brier_score",
        "roc_auc",
        "recall_at_5",
        "recall_at_10",
        "episode_recall",
        "false_alerts_per_true_alert",
        "no_clear_leader_rate",
    }
    assert set(schema["properties"]["threshold_policy"]["required"]) >= {
        "publish_top_n",
        "publish_threshold",
        "alert_threshold",
    }


def test_json_schema_contracts_stay_in_sync_with_python_models() -> None:
    snapshot_schema = _load_json(CONTRACT_DIR / "website_snapshot.schema.json")
    model_card_schema = _load_json(CONTRACT_DIR / "model_card.schema.json")

    manifest_required = set(snapshot_schema["properties"]["manifest"]["required"])
    forecast_required = set(snapshot_schema["properties"]["forecast_snapshot"]["required"])
    country_required = set(snapshot_schema["properties"]["forecast_snapshot"]["properties"]["countries"]["items"]["required"])
    metrics_required = set(model_card_schema["properties"]["metrics"]["required"])
    freshness_enum = set(
        snapshot_schema["properties"]["forecast_snapshot"]["properties"]["countries"]["items"]["properties"]["freshness_tier"][
            "enum"
        ]
    )

    assert manifest_required <= set(WebsiteSnapshotManifest.model_fields)
    assert forecast_required <= set(ForecastSnapshot.model_fields)
    assert country_required <= {"iso3", "country_name", "region_name", "score", "delta", "forecast_as_of", "freshness_tier", "rank"}
    assert metrics_required <= set(ModelCardMetrics.model_fields)
    assert freshness_enum == {tier.value for tier in FreshnessTier}
    assert WebsiteSnapshotManifest.model_fields["schema_version"].default == "1.0.0"


def test_example_bundle_validates_against_python_contract() -> None:
    payload = _load_json(EXAMPLE_PATH)

    bundle = WebsiteSnapshotBundle.model_validate(payload)
    model_card = ModelCardPayload.model_validate(payload["model_card"])

    assert bundle.manifest.baseline_used is False
    assert bundle.manifest.predicted_conflict.label == "Lebanon / Israel"
    assert bundle.manifest.provenance.onset.training.run_name == "train_country_week_onset_logit_30d"
    assert bundle.manifest.provenance.escalation.training.run_name == "train_country_week_logit_30d"
    assert bundle.manifest.provenance.structural.training.run_name == "train_country_week_onset_structural_90d"
    assert bundle.forecast_snapshot.primary_target == "onset"
    assert bundle.forecast_snapshot.alert_type == "Onset Watch"
    assert bundle.forecast_snapshot.countries[0].iso3 == bundle.forecast_snapshot.lead_country_iso3
    assert bundle.forecast_snapshot.countries[0].freshness_tier == "fresh"
    assert model_card.threshold_policy.publish_threshold == 0.82
    assert model_card.metrics.episode_recall == 0.44
    assert model_card.metrics.roc_auc == 0.81
