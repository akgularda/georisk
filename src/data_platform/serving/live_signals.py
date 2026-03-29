from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_zscore(series: pd.Series) -> pd.Series:
    series = series.fillna(0.0).astype(float)
    std = series.std(ddof=0)
    if std == 0 or np.isnan(std):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.mean()) / std


def build_gold_country_live_signals(
    events: pd.DataFrame,
    documents: pd.DataFrame,
    unhcr_origin_population: pd.DataFrame,
) -> pd.DataFrame:
    latest_event_date = events["event_date"].dropna().max()
    latest_document_date = documents["document_date"].dropna().max()
    current_date = max(filter(pd.notna, [latest_event_date, latest_document_date]))

    current_events = events.loc[events["event_date"] == latest_event_date].groupby("country_id", dropna=False).agg(
        current_event_count=("global_event_id", "count"),
        current_avg_goldstein=("goldstein_scale", "mean"),
        current_avg_event_tone=("avg_tone", "mean"),
    )
    trailing_events = events.loc[
        events["event_date"].between(latest_event_date - pd.Timedelta(days=6), latest_event_date)
    ].groupby("country_id", dropna=False).agg(
        trailing_7d_event_count=("global_event_id", "count"),
        trailing_7d_avg_goldstein=("goldstein_scale", "mean"),
    )

    current_documents = documents.loc[documents["document_date"] == latest_document_date].groupby(
        "document_country_id", dropna=False
    ).agg(
        current_document_count=("document_identifier", "count"),
        current_avg_document_tone=("tone_score", "mean"),
    )
    trailing_documents = documents.loc[
        documents["document_date"].between(latest_document_date - pd.Timedelta(days=6), latest_document_date)
    ].groupby("document_country_id", dropna=False).agg(
        trailing_7d_document_count=("document_identifier", "count"),
        trailing_7d_avg_document_tone=("tone_score", "mean"),
    )

    gold = (
        current_events.join(trailing_events, how="outer")
        .join(current_documents, how="outer")
        .join(trailing_documents, how="outer")
        .join(unhcr_origin_population.set_index("country_id"), how="left")
        .reset_index()
        .rename(columns={"index": "country_id", "document_country_id": "country_id"})
    )
    if "document_country_id" in gold.columns:
        gold["country_id"] = gold["country_id"].fillna(gold["document_country_id"])
        gold = gold.drop(columns=["document_country_id"])
    gold["as_of_date"] = current_date
    gold["live_signal_score"] = (
        _safe_zscore(gold["current_event_count"])
        + _safe_zscore(-gold["current_avg_document_tone"].fillna(0.0))
        + _safe_zscore(gold["idps"].fillna(0.0))
    )
    return gold.sort_values(by="live_signal_score", ascending=False, na_position="last").reset_index(drop=True)
