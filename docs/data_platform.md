# Data Platform

This package now has two implemented real-source data pipelines and one explicit Phase A contract layer:

- `live_country_signals`: a current-country monitoring slice built from `GDELT` and `UNHCR`
- `country_week_features`: a prompt-aligned weekly master-table slice built from `ACLED`, `FAO`, `GDELT`, `IDEA`, `IMF`, `NASA Black Marble`, `NOAA`, `SIPRI`, `UN Comtrade`, `UNCTAD`, `UCDP GED`, `WGI`, `World Bank WDI`, and `UNHCR`
- `source_registry.yaml`: the explicit Phase A source contract from `06_data_sources_catalog.md`

The current implementation still only covers a subset of the full Phase A catalog, but the registry now makes that gap explicit. Both implemented paths preserve raw manifests, write bronze and silver layers, and publish gold outputs through the same CLI entrypoint.

## Run commands

Run the live country-signal pipeline:

```bash
python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_live_country_signals.yaml
```

Run the weekly master-table pipeline:

```bash
python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml
```

Run either pipeline against saved real-source snapshots:

```bash
python -m src.data_platform.orchestration.cli run --config configs/data_platform/pipeline_country_week_features.yaml --use-test-snapshots
```

## Phase A source registry

The registry lives at `configs/data_platform/source_registry.yaml` and currently tracks:

- readiness: `implemented`, `stubbed`, `missing`
- access requirement: `open`, `account_required`
- snapshot requirement: `none`, `snapshot_required`

This is a contract map, not a claim that the missing sources are already wired.

## Current source coverage

Implemented now:

- `ACLED` via local snapshot/file-drop CSVs
- `FAO` via local snapshot/file-drop CSVs
- `GDELT` via raw `gdeltv2` file downloads
- `IDEA` via local snapshot/file-drop CSVs
- `IMF` via local snapshot/file-drop CSVs
- `NASA Black Marble` via local snapshot/file-drop CSVs
- `NOAA` via local snapshot/file-drop CSVs
- `SIPRI` via local snapshot/file-drop CSVs
- `UN Comtrade` via local snapshot/file-drop CSVs
- `UNCTAD` via local snapshot/file-drop CSVs
- `UNHCR population API` via origin-country population records
- `World Bank WDI API` for GDP growth, CPI inflation, and total population
- `WGI` via local snapshot/file-drop CSVs
- `UCDP GED` via the official GED CSV zip download

Defined but not implemented yet:

- `V-Dem`
- market and logistics placeholders for `FX`, `spreads`, `energy`, and `commodities`

## Storage layers

### Raw

- `data/raw/<run_name>/raw_manifest.json`
- upstream URLs, snapshot file paths, and source last-update metadata

### Bronze

- `data/bronze/acled/`
- `data/bronze/gdelt/`
- `data/bronze/idea/`
- `data/bronze/nasa_black_marble/`
- `data/bronze/noaa/`
- `data/bronze/sipri/`
- `data/bronze/un_comtrade/`
- `data/bronze/unctad/`
- `data/bronze/unhcr/`
- `data/bronze/wdi/`
- `data/bronze/wgi/`
- `data/bronze/ucdp/`

Bronze keeps lightly parsed source fidelity, before contract normalization.

### Silver

- `data/silver/acled/events.parquet`
- `data/silver/gdelt/events.parquet`
- `data/silver/gdelt/gkg_documents.parquet`
- `data/silver/idea/elections.parquet`
- `data/silver/nasa_black_marble/night_lights_series.parquet`
- `data/silver/noaa/climate_series.parquet`
- `data/silver/sipri/security_series.parquet`
- `data/silver/un_comtrade/trade_series.parquet`
- `data/silver/unctad/shipping_series.parquet`
- `data/silver/unhcr/origin_population.parquet`
- `data/silver/wdi/indicator_series.parquet`
- `data/silver/wdi/country_year_snapshot.parquet`
- `data/silver/wgi/country_year_snapshot.parquet`
- `data/silver/ucdp/events.parquet`

### Gold

- `data/gold/live_country_signals/gold_country_live_signals.parquet`
- `data/gold/country_week_features/country_week_features.parquet`
- `gold_entity_day_features`
- `gold_entity_day_labels`
- `gold_report_inputs`
- `gold_social_inputs`

The weekly pipeline now also writes:

- `data/gold/entity_day_features/entity_day_features.parquet`
- `data/gold/entity_day_labels/entity_day_labels.parquet`
- `data/gold/report_inputs/report_inputs.parquet`
- `data/gold/social_inputs/social_inputs.parquet`

Each gold directory includes its own `validation_report.json`. The consolidated `country_week_features` validation report also includes entries for the four downstream gold tables.

## Current contracts

### Silver WDI indicator series

- `source_name`
- `country_iso3`
- `country_name`
- `indicator_id`
- `indicator_name`
- `year`
- `value`
- `frequency`
- `publication_ts_utc`
- `ingestion_ts_utc`

### Silver IMF commodity series

- `source_name`
- `source_record_id`
- `observation_date`
- `market_oil_price_usd_per_barrel`
- `market_gas_price_index`
- `market_fertilizer_price_index`
- `market_commodity_price_index`
- `publication_ts_utc`
- `ingestion_ts_utc`

### Silver FAO food-price series

- `source_name`
- `source_record_id`
- `observation_date`
- `food_price_index`
- `food_cereal_price_index`
- `publication_ts_utc`
- `ingestion_ts_utc`

### Silver WGI country-year snapshot

- `source_name`
- `source_record_id`
- `country_iso3`
- `country_name`
- `year`
- `governance_voice_and_accountability`
- `governance_political_stability`
- `governance_government_effectiveness`
- `governance_regulatory_quality`
- `governance_rule_of_law`
- `governance_control_of_corruption`
- `governance_score`
- `publication_ts_utc`
- `ingestion_ts_utc`

### Silver IDEA election calendar

- `source_name`
- `source_record_id`
- `country_iso3`
- `country_name`
- `election_date`
- `election_type`
- `election_name`
- `status`
- `publication_ts_utc`
- `ingestion_ts_utc`

### Silver ACLED events

- `source_name`
- `source_record_id`
- `country_iso3`
- `country_name`
- `admin1_name`
- `admin2_name`
- `location_name`
- `event_date`
- `publication_ts_utc`
- `ingestion_ts_utc`
- `event_type`
- `sub_event_type`
- `event_type_slug`
- `sub_event_type_slug`
- `actor1_name`
- `actor1_associated_actor_name`
- `actor2_name`
- `actor2_associated_actor_name`
- `fatalities`
- `notes`
- `latitude`
- `longitude`
- `source`

### Silver UCDP GED events

- `source_name`
- `source_record_id`
- `country_iso3`
- `country_name`
- `region_name`
- `admin1_name`
- `admin2_name`
- `event_date_start`
- `event_date_end`
- `publication_ts_utc`
- `ingestion_ts_utc`
- `event_type`
- `type_of_violence`
- `conflict_name`
- `side_a`
- `side_b`
- `best_fatalities`
- `high_fatalities`
- `low_fatalities`
- `latitude`
- `longitude`
- `location_precision`
- `year`

### Gold country-week features

- `country_iso3`
- `week_start_date`
- `label_escalation_7d`
- `label_escalation_30d`
- `label_onset_30d`
- `label_interstate_30d`
- `acled_event_count_7d`
- `acled_fatalities_sum_7d`
- `acled_protest_count_7d`
- `acled_riot_count_7d`
- `acled_violence_against_civilians_count_7d`
- `acled_explosions_remote_violence_count_7d`
- `acled_strategic_developments_count_7d`
- `acled_distinct_actor1_count_7d`
- `acled_distinct_actor2_count_7d`
- `acled_event_count_28d`
- `acled_fatalities_sum_28d`
- `market_oil_price_usd_per_barrel`
- `market_gas_price_index`
- `market_fertilizer_price_index`
- `market_commodity_price_index`
- `food_price_index`
- `food_cereal_price_index`
- `trade_exports_value_usd`
- `trade_imports_value_usd`
- `trade_exports_3m_change_pct`
- `trade_imports_3m_change_pct`
- `shipping_lsci_index`
- `shipping_port_connectivity_index`
- `gdelt_event_count_7d`
- `gdelt_avg_goldstein_7d`
- `gdelt_avg_event_tone_7d`
- `gdelt_num_mentions_7d`
- `gdelt_num_articles_7d`
- `gdelt_document_count_7d`
- `gdelt_avg_document_tone_7d`
- `governance_voice_and_accountability`
- `governance_political_stability`
- `governance_government_effectiveness`
- `governance_regulatory_quality`
- `governance_rule_of_law`
- `governance_control_of_corruption`
- `governance_score`
- `days_to_next_election`
- `days_since_last_election`
- `election_upcoming_30d`
- `election_upcoming_90d`
- `election_recent_30d`
- `election_recent_90d`
- `climate_drought_severity_index`
- `climate_temperature_anomaly_c`
- `climate_precipitation_anomaly_pct`
- `climate_night_lights_anomaly_pct`
- `climate_night_lights_zscore`
- `security_military_expenditure_usd`
- `security_military_expenditure_pct_gdp`
- `security_arms_import_volume_index`
- `ucdp_history_event_count_52w`
- `ucdp_history_best_deaths_52w`
- `ucdp_history_state_based_events_52w`
- `macro_gdp_growth_annual_pct`
- `macro_cpi_yoy`
- `macro_population_total`
- `humanitarian_refugees`
- `humanitarian_asylum_seekers`
- `humanitarian_idps`
- `snapshot_ts_utc`

This is the first real `country_week_features` contract, not the final full catalog target.

### Gold serving contracts

The contract names are:

- `gold_country_week_features`
- `gold_entity_day_features`
- `gold_entity_day_labels`
- `gold_report_inputs`
- `gold_social_inputs`

All five serving contracts are now implemented. The downstream four are intentionally thin first cuts derived directly from the dense weekly country table, with `country_iso3` used as the initial entity identifier.

### Gold entity-day features

- Minimum contract columns:
- `entity_id`
- `entity_type`
- `country_iso3`
- `country_name`
- `feature_date`
- `source_week_start_date`

This table expands each weekly country row into seven daily rows while preserving the originating week pointer. The current implementation also emits thin convenience metadata such as `entity_name`, `region_name`, selected feature values, `snapshot_ts_utc`, and `feature_snapshot_hash`.

### Gold entity-day labels

- Minimum contract columns:
- `entity_id`
- `country_iso3`
- `label_date`
- `horizon_days`
- `label_escalation_7d`
- `label_escalation_30d`
- `label_onset_30d`

This table expands the implemented weekly labels across the same seven-day span as a wide daily table. It has one row per country-day-horizon, with unknown future labels left null when the weekly source row is not yet fully observed. The current implementation also carries `entity_name`, `entity_type`, `country_name`, `source_week_start_date`, and `snapshot_ts_utc`.

### Gold report inputs

- Minimum contract columns:
- `country_iso3`
- `country_name`
- `region_name`
- `report_date`
- `risk_level`
- `freshness_days`
- `summary`
- `chronology`

This is a deterministic latest-country report layer built from the latest weekly row per country, not yet from forecast artifacts. When the latest weekly row still has unknown forward labels, `forecast_probability` and `risk_level` remain null rather than treating unknown outcomes as observed negatives. The current implementation also emits identifiers, slug/title fields, forecast metadata, top-driver payloads, and snapshot hashes as convenience columns.

### Gold social inputs

- Minimum contract columns:
- `country_iso3`
- `country_name`
- `publish_date`
- `score_delta`
- `summary_line`
- `top_drivers`
- `report_slug`

This is a deterministic social-ready latest-country layer built from the same latest weekly row per country. When the latest weekly row still has unknown forward labels, forecast-like fields remain null and the rendered copy switches to neutral awaiting-outcome wording. The current implementation also emits posting identifiers, platform metadata, forecast metadata, rendered copy, and snapshot hashes as convenience columns.

## Point-in-time behavior

- `GDELT` keeps `event_date` and `published_at`
- `UCDP GED` keeps `event_date_start`, `event_date_end`, `publication_ts_utc`, and `ingestion_ts_utc`
- `WDI` keeps `publication_ts_utc` from the World Bank response metadata and `ingestion_ts_utc`
- `UNHCR` keeps source-year alignment, but the public population endpoint is annual and does not expose revision timestamps at the record level
- the source registry separates readiness from access and snapshot requirements so ACLED can be implemented but account-gated, while SIPRI / NOAA / NASA Black Marble are implemented through versioned snapshot paths

The weekly gold table joins annual macro and humanitarian series using the latest source year less than or equal to the prediction week year.

## Validation

Validation reports currently check:

- row counts
- output columns
- null counts on key contract columns

The pipeline still needs stricter business-rule validation for:

- duplicate source-record checks
- source freshness thresholds
- coordinate sanity and bounding checks
- hard failure on unmapped geography codes

## Known gaps

- `label_interstate_30d` is present in the contract but still null because no interstate-specific label builder has been added yet.
- `country_week_features` currently covers implemented blocks: `acled_*`, `gdelt_*`, `ucdp_history_*`, `macro_*`, `humanitarian_*`, `market_*`, `food_*`, `trade_*`, `shipping_*`, `governance_*`, `election_*`, `climate_*`, and `security_*`.
- digital repression and spillover blocks still need additional source connectors and feature builders.
- the current downstream serving contracts still use country-level entities; no finer entity grain is published yet.
- GDELT country assignment still depends partly on place-name resolution.
