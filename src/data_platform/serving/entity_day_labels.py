from __future__ import annotations

import pandas as pd


ENTITY_DAY_LABEL_COLUMNS = [
    "entity_id",
    "entity_name",
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
    "label_interstate_30d",
    "label_interstate_onset_30d",
    "label_interstate_onset_90d",
    "snapshot_ts_utc",
]

_HORIZON_LABEL_COLUMNS = {
    7: ("label_escalation_7d",),
    30: ("label_escalation_30d", "label_onset_30d", "label_interstate_30d", "label_interstate_onset_30d"),
    90: ("label_onset_90d", "label_interstate_onset_90d"),
}


def _empty_entity_day_labels() -> pd.DataFrame:
    return pd.DataFrame(columns=ENTITY_DAY_LABEL_COLUMNS)


def build_gold_entity_day_labels(country_week_features: pd.DataFrame) -> pd.DataFrame:
    if country_week_features.empty:
        return _empty_entity_day_labels()

    weekly = country_week_features.copy()
    weekly["week_start_date"] = pd.to_datetime(weekly["week_start_date"], errors="coerce")
    records: list[dict[str, object]] = []

    for _, row in weekly.iterrows():
        for day_offset in range(7):
            label_date = (pd.Timestamp(row["week_start_date"]) + pd.Timedelta(days=day_offset)).date()
            for horizon_days, active_columns in _HORIZON_LABEL_COLUMNS.items():
                records.append(
                    {
                        "entity_id": row["country_iso3"],
                        "entity_name": row["country_name"],
                        "entity_type": "country",
                        "country_iso3": row["country_iso3"],
                        "country_name": row["country_name"],
                        "label_date": label_date,
                        "source_week_start_date": pd.Timestamp(row["week_start_date"]).date(),
                        "horizon_days": horizon_days,
                        "label_escalation_7d": row.get("label_escalation_7d") if "label_escalation_7d" in active_columns else pd.NA,
                        "label_escalation_30d": row.get("label_escalation_30d") if "label_escalation_30d" in active_columns else pd.NA,
                        "label_onset_30d": row.get("label_onset_30d") if "label_onset_30d" in active_columns else pd.NA,
                        "label_onset_90d": row.get("label_onset_90d") if "label_onset_90d" in active_columns else pd.NA,
                        "label_interstate_30d": row.get("label_interstate_30d") if "label_interstate_30d" in active_columns else pd.NA,
                        "label_interstate_onset_30d": row.get("label_interstate_onset_30d") if "label_interstate_onset_30d" in active_columns else pd.NA,
                        "label_interstate_onset_90d": row.get("label_interstate_onset_90d") if "label_interstate_onset_90d" in active_columns else pd.NA,
                        "snapshot_ts_utc": row.get("snapshot_ts_utc"),
                    }
                )

    entity_day_labels = pd.DataFrame.from_records(records).sort_values(["country_iso3", "label_date", "horizon_days"]).reset_index(drop=True)
    return entity_day_labels[ENTITY_DAY_LABEL_COLUMNS]
