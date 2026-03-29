from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.data_platform.orchestration.pipeline import run_country_week_features_pipeline


def test_country_week_features_pipeline_from_real_snapshots(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[3]
    result = run_country_week_features_pipeline(
        project_root / "configs" / "data_platform" / "pipeline_country_week_features.yaml",
        output_root=tmp_path,
        use_test_snapshots=True,
    )

    assert result.raw_manifest_file.exists()
    assert result.validation_report_file.exists()
    assert result.gold_country_week_features_file.exists()
    assert result.gold_entity_day_features_file.exists()
    assert result.gold_entity_day_features_validation_report_file.exists()
    assert result.gold_entity_day_labels_file.exists()
    assert result.gold_entity_day_labels_validation_report_file.exists()
    assert result.gold_report_inputs_file.exists()
    assert result.gold_report_inputs_validation_report_file.exists()
    assert result.gold_social_inputs_file.exists()
    assert result.gold_social_inputs_validation_report_file.exists()

    gold = pd.read_parquet(result.gold_country_week_features_file)
    assert not gold.empty
    assert {"country_iso3", "country_name", "region_name", "week_start_date", "snapshot_ts_utc"}.issubset(gold.columns)
    assert "market_oil_price_usd_per_barrel" in gold.columns
    assert "food_price_index" in gold.columns
    assert "trade_exports_value_usd" in gold.columns
    assert "shipping_lsci_index" in gold.columns
    assert "macro_gdp_growth_annual_pct" in gold.columns
    assert "climate_drought_severity_index" in gold.columns
    assert "climate_night_lights_anomaly_pct" in gold.columns
    assert "security_military_expenditure_usd" in gold.columns
    assert "acled_event_count_7d" in gold.columns
    assert "acled_event_count_28d" in gold.columns
    assert "gdelt_event_count_28d" in gold.columns
    assert "gdelt_document_count_28d" in gold.columns
    assert "gdelt_event_count_7d_delta" in gold.columns
    assert "gdelt_document_count_7d_delta" in gold.columns
    assert "acled_event_count_7d_delta" in gold.columns
    assert "acled_fatalities_sum_7d_delta" in gold.columns
    assert "acled_protest_count_7d_delta" in gold.columns
    assert "acled_riot_count_7d_delta" in gold.columns
    assert "organized_violence_quiet_56d" in gold.columns
    assert "governance_score" in gold.columns
    assert "days_to_next_election" in gold.columns
    assert "label_onset_90d" in gold.columns
    assert "label_interstate_onset_30d" in gold.columns
    assert "label_interstate_onset_90d" in gold.columns
    assert gold["label_onset_90d"].isna().any()
    assert gold["label_interstate_30d"].equals(gold["label_interstate_onset_30d"])

    weekly_span = pd.date_range(
        pd.Timestamp(gold["week_start_date"].min()),
        pd.Timestamp(gold["week_start_date"].max()),
        freq="W-MON",
    )
    group_sizes = gold.groupby("country_iso3")["week_start_date"].size()
    assert group_sizes.nunique() == 1
    assert group_sizes.iloc[0] == len(weekly_span)

    colombia = gold.loc[gold["country_iso3"] == "COL"]
    assert len(colombia) == len(weekly_span)
    assert colombia["country_name"].eq("Colombia").all()
    assert colombia["acled_event_count_7d"].eq(0).all()
    assert colombia["macro_population_total"].notna().all()

    entity_day_features = pd.read_parquet(result.gold_entity_day_features_file)
    assert not entity_day_features.empty
    assert {
        "entity_id",
        "entity_type",
        "country_iso3",
        "country_name",
        "feature_date",
        "source_week_start_date",
        "snapshot_ts_utc",
    }.issubset(entity_day_features.columns)
    assert entity_day_features["entity_id"].equals(entity_day_features["country_iso3"])
    assert entity_day_features["entity_type"].eq("country").all()

    entity_day_labels = pd.read_parquet(result.gold_entity_day_labels_file)
    assert not entity_day_labels.empty
    assert {
        "entity_id",
        "entity_type",
        "country_iso3",
        "country_name",
        "label_date",
        "source_week_start_date",
        "horizon_days",
        "label_escalation_7d",
        "label_escalation_30d",
        "label_onset_30d",
        "label_onset_90d",
        "label_interstate_onset_30d",
        "label_interstate_onset_90d",
        "snapshot_ts_utc",
    }.issubset(entity_day_labels.columns)
    assert "target_name" not in entity_day_labels.columns
    assert "label_value" not in entity_day_labels.columns
    assert set(entity_day_labels["horizon_days"].unique()) == {7, 30, 90}
    assert not entity_day_labels.duplicated(subset=["entity_id", "label_date", "horizon_days"]).any()
    assert entity_day_labels.loc[entity_day_labels["horizon_days"] == 90, "label_onset_90d"].notna().any()
    assert "ucdp_onset" in json.loads(result.raw_manifest_file.read_text(encoding="utf-8"))

    report_inputs = pd.read_parquet(result.gold_report_inputs_file)
    assert not report_inputs.empty
    assert {
        "country_iso3",
        "country_name",
        "region_name",
        "report_date",
        "risk_level",
        "freshness_days",
        "summary",
        "chronology",
    }.issubset(report_inputs.columns)
    assert report_inputs["country_iso3"].is_unique

    social_inputs = pd.read_parquet(result.gold_social_inputs_file)
    assert not social_inputs.empty
    assert {
        "country_iso3",
        "country_name",
        "publish_date",
        "score_delta",
        "summary_line",
        "top_drivers",
        "report_slug",
    }.issubset(social_inputs.columns)
    assert social_inputs["country_iso3"].is_unique

    entity_day_features_validation = json.loads(result.gold_entity_day_features_validation_report_file.read_text(encoding="utf-8"))
    entity_day_labels_validation = json.loads(result.gold_entity_day_labels_validation_report_file.read_text(encoding="utf-8"))
    report_inputs_validation = json.loads(result.gold_report_inputs_validation_report_file.read_text(encoding="utf-8"))
    social_inputs_validation = json.loads(result.gold_social_inputs_validation_report_file.read_text(encoding="utf-8"))
    consolidated_validation = json.loads(result.validation_report_file.read_text(encoding="utf-8"))

    assert entity_day_features_validation["tables"][0]["table_name"] == "gold_entity_day_features"
    assert entity_day_labels_validation["tables"][0]["table_name"] == "gold_entity_day_labels"
    assert report_inputs_validation["tables"][0]["table_name"] == "gold_report_inputs"
    assert social_inputs_validation["tables"][0]["table_name"] == "gold_social_inputs"
    assert {"gold_country_week_features", "gold_entity_day_features", "gold_entity_day_labels", "gold_report_inputs", "gold_social_inputs"}.issubset(
        {table["table_name"] for table in consolidated_validation["tables"]}
    )
