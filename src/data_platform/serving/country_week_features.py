from __future__ import annotations

from collections.abc import Iterable
from datetime import date

import numpy as np
import pandas as pd

from src.data_platform.serving.panel import build_country_dimension, build_country_week_panel, build_weekly_date_index
from src.data_platform.serving.ucdp_onset import localize_ucdp_country_onsets


def _ensure_timestamp(value: pd.Timestamp | str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _week_start_from_series(series: pd.Series) -> pd.Series:
    normalized = pd.to_datetime(series, errors="coerce").dt.normalize()
    return normalized - pd.to_timedelta(normalized.dt.weekday, unit="D")


def _week_start_from_timestamp(value: pd.Timestamp | str) -> pd.Timestamp:
    timestamp = _ensure_timestamp(value).tz_localize(None).normalize()
    return timestamp - pd.Timedelta(days=timestamp.weekday())


def _country_weeks_from_rows(frame: pd.DataFrame, country_column: str, date_column: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["country_iso3", "week_start_date"])
    base = frame.loc[frame[country_column].notna() & frame[date_column].notna(), [country_column, date_column]].copy()
    base["week_start_date"] = _week_start_from_series(base[date_column])
    return base.rename(columns={country_column: "country_iso3"})[["country_iso3", "week_start_date"]].drop_duplicates()


def _aggregate_gdelt_events(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["country_iso3", "week_start_date", "gdelt_event_count_7d"])
    events = frame.loc[frame["country_id"].notna() & frame["event_date"].notna()].copy()
    events["country_iso3"] = events["country_id"]
    events["week_start_date"] = _week_start_from_series(events["event_date"])
    return (
        events.groupby(["country_iso3", "week_start_date"], dropna=False)
        .agg(
            gdelt_event_count_7d=("global_event_id", "count"),
            gdelt_avg_goldstein_7d=("goldstein_scale", "mean"),
            gdelt_avg_event_tone_7d=("avg_tone", "mean"),
            gdelt_num_mentions_7d=("num_mentions", "sum"),
            gdelt_num_articles_7d=("num_articles", "sum"),
        )
        .reset_index()
    )


def _aggregate_gdelt_documents(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["country_iso3", "week_start_date", "gdelt_document_count_7d"])
    documents = frame.loc[frame["document_country_id"].notna() & frame["document_date"].notna()].copy()
    documents["country_iso3"] = documents["document_country_id"]
    documents["week_start_date"] = _week_start_from_series(documents["document_date"])
    return (
        documents.groupby(["country_iso3", "week_start_date"], dropna=False)
        .agg(
            gdelt_document_count_7d=("document_identifier", "count"),
            gdelt_avg_document_tone_7d=("tone_score", "mean"),
        )
        .reset_index()
    )


def _aggregate_acled_event_types(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["country_iso3", "week_start_date"])
    events = frame.loc[frame["country_iso3"].notna() & frame["event_date"].notna()].copy()
    events["week_start_date"] = _week_start_from_series(events["event_date"])
    events["fatalities"] = pd.to_numeric(events["fatalities"], errors="coerce").fillna(0)
    events["actor1_name"] = events["actor1_name"].astype("string")
    events["actor2_name"] = events["actor2_name"].astype("string")

    def _count_type(slug: str) -> pd.Series:
        return (events["event_type_slug"] == slug).astype(int)

    grouped = (
        events.assign(
            is_protest=_count_type("protests"),
            is_riot=_count_type("riots"),
            is_vac=_count_type("violence_against_civilians"),
            is_explosion=_count_type("explosions_remote_violence"),
            is_strategic=_count_type("strategic_developments"),
        )
        .groupby(["country_iso3", "week_start_date"], dropna=False)
        .agg(
            acled_event_count_7d=("source_record_id", "count"),
            acled_fatalities_sum_7d=("fatalities", "sum"),
            acled_protest_count_7d=("is_protest", "sum"),
            acled_riot_count_7d=("is_riot", "sum"),
            acled_violence_against_civilians_count_7d=("is_vac", "sum"),
            acled_explosions_remote_violence_count_7d=("is_explosion", "sum"),
            acled_strategic_developments_count_7d=("is_strategic", "sum"),
            acled_distinct_actor1_count_7d=("actor1_name", lambda series: series.dropna().nunique()),
            acled_distinct_actor2_count_7d=("actor2_name", lambda series: series.dropna().nunique()),
        )
        .reset_index()
    )
    return grouped


def _select_latest_year_row(frame: pd.DataFrame, country_iso3: str, year: int) -> dict[str, object]:
    country_rows = frame.loc[(frame["country_iso3"] == country_iso3) & (frame["year"] <= year)].sort_values(by="year", ascending=False)
    if country_rows.empty:
        return {}
    return country_rows.iloc[0].to_dict()


def _select_latest_country_row(frame: pd.DataFrame, country_iso3: str, date_column: str, cutoff_date: pd.Timestamp) -> dict[str, object]:
    if frame.empty:
        return {}
    observation_dates = pd.to_datetime(frame[date_column], errors="coerce").dt.normalize()
    candidate_rows = frame.loc[(frame["country_iso3"] == country_iso3) & (observation_dates <= cutoff_date)].copy()
    if candidate_rows.empty:
        return {}
    candidate_rows["_observation_date"] = observation_dates.loc[candidate_rows.index]
    candidate_rows = candidate_rows.sort_values(by="_observation_date", ascending=False)
    return candidate_rows.iloc[0].to_dict()


def _select_latest_global_row(frame: pd.DataFrame, date_column: str, cutoff_date: pd.Timestamp) -> dict[str, object]:
    if frame.empty:
        return {}
    observation_dates = pd.to_datetime(frame[date_column], errors="coerce").dt.normalize()
    candidate_rows = frame.loc[observation_dates <= cutoff_date].copy()
    if candidate_rows.empty:
        return {}
    candidate_rows["_observation_date"] = observation_dates.loc[candidate_rows.index]
    candidate_rows = candidate_rows.sort_values(by="_observation_date", ascending=False)
    return candidate_rows.iloc[0].to_dict()


def _build_asof_row_lookup(
    frame: pd.DataFrame,
    date_column: str,
    week_starts: Iterable[pd.Timestamp],
) -> dict[pd.Timestamp, dict[str, object]]:
    if frame.empty:
        return {}
    observations = frame.copy()
    observations[date_column] = pd.to_datetime(observations[date_column], errors="coerce").dt.normalize()
    observations = observations.loc[observations[date_column].notna()].sort_values(by=date_column).reset_index(drop=True)
    if observations.empty:
        return {}
    week_frame = pd.DataFrame({"week_start_date": pd.to_datetime(list(week_starts), errors="coerce")}).sort_values(
        by="week_start_date"
    )
    merged = pd.merge_asof(
        week_frame,
        observations,
        left_on="week_start_date",
        right_on=date_column,
        direction="backward",
    )
    lookup: dict[pd.Timestamp, dict[str, object]] = {}
    for _, row in merged.iterrows():
        if pd.isna(row.get(date_column)):
            lookup[row["week_start_date"]] = {}
            continue
        row_dict = row.to_dict()
        row_dict.pop("week_start_date", None)
        lookup[row["week_start_date"]] = row_dict
    return lookup


def _build_latest_year_row_lookup(frame: pd.DataFrame, years: Iterable[int]) -> dict[int, dict[str, object]]:
    if frame.empty:
        return {}
    observations = frame.copy()
    observations["year"] = pd.to_numeric(observations["year"], errors="coerce").astype("Int64")
    observations = observations.loc[observations["year"].notna()].sort_values(by="year").reset_index(drop=True)
    if observations.empty:
        return {}
    lookup: dict[int, dict[str, object]] = {}
    records = observations.to_dict("records")
    current: dict[str, object] = {}
    index = 0
    for year in sorted(set(int(year) for year in years)):
        while index < len(records) and int(records[index]["year"]) <= year:
            current = records[index]
            index += 1
        lookup[year] = current.copy() if current else {}
    return lookup


def _build_election_date_lookup(
    frame: pd.DataFrame,
    week_starts: Iterable[pd.Timestamp],
) -> dict[pd.Timestamp, tuple[pd.Timestamp | pd.NaT, pd.Timestamp | pd.NaT]]:
    if frame.empty:
        return {}
    election_dates = pd.to_datetime(frame["election_date"], errors="coerce").dropna().sort_values().to_numpy()
    if len(election_dates) == 0:
        return {}
    lookup: dict[pd.Timestamp, tuple[pd.Timestamp | pd.NaT, pd.Timestamp | pd.NaT]] = {}
    for week_start in week_starts:
        next_index = election_dates.searchsorted(week_start.to_datetime64(), side="left")
        last_index = election_dates.searchsorted(week_start.to_datetime64(), side="right") - 1
        next_election_date = pd.Timestamp(election_dates[next_index]) if next_index < len(election_dates) else pd.NaT
        last_election_date = pd.Timestamp(election_dates[last_index]) if last_index >= 0 else pd.NaT
        lookup[week_start] = (next_election_date, last_election_date)
    return lookup


def _select_nearest_future_date(frame: pd.DataFrame, week_start: pd.Timestamp) -> pd.Timestamp | pd.NaT:
    future_rows = frame.loc[frame["election_date"] >= week_start].sort_values(by="election_date", ascending=True)
    if future_rows.empty:
        return pd.NaT
    return future_rows.iloc[0]["election_date"]


def _select_nearest_past_date(frame: pd.DataFrame, week_start: pd.Timestamp) -> pd.Timestamp | pd.NaT:
    past_rows = frame.loc[frame["election_date"] <= week_start].sort_values(by="election_date", ascending=False)
    if past_rows.empty:
        return pd.NaT
    return past_rows.iloc[0]["election_date"]


def _to_nullable_days(delta: pd.Timedelta | None) -> int | pd.NAType:
    if delta is None or pd.isna(delta):
        return pd.NA
    return int(delta.days)


def _within_days(days: int | pd.NAType, window: int) -> int:
    if pd.isna(days):
        return 0
    return int(int(days) <= window)


def _as_int_or_na(value: bool | None) -> int | pd.NAType:
    if value is None:
        return pd.NA
    return int(bool(value))


def _as_known_int_or_na(value: bool, *, is_known: bool) -> int | pd.NAType:
    if not is_known:
        return pd.NA
    return int(bool(value))


def _delta_from_short_long(short_window_total: float, long_window_total: float, periods: int) -> float:
    if periods <= 0:
        return float(short_window_total)
    return float(short_window_total) - (float(long_window_total) / float(periods))


def _window_bounds(dates: np.ndarray, start: pd.Timestamp, end: pd.Timestamp) -> tuple[int, int]:
    left = int(dates.searchsorted(np.datetime64(start.to_datetime64()), side="left"))
    right = int(dates.searchsorted(np.datetime64(end.to_datetime64()), side="right"))
    return left, right


def _prefix_sum(values: np.ndarray) -> np.ndarray:
    return np.concatenate(([0.0], np.cumsum(values.astype(float, copy=False))))


def _window_sum(prefix: np.ndarray, left: int, right: int) -> float:
    return float(prefix[right] - prefix[left])


def _window_mean(prefix: np.ndarray, left: int, right: int) -> float:
    count = right - left
    if count <= 0:
        return float("nan")
    return _window_sum(prefix, left, right) / float(count)


def _window_unique_count(values: np.ndarray, left: int, right: int) -> int:
    if right <= left:
        return 0
    window = values[left:right]
    if len(window) == 0:
        return 0
    return int(pd.Series(window, dtype="string").dropna().nunique())


COUNTRY_WEEK_FEATURE_COLUMNS = [
    "country_iso3",
    "country_name",
    "region_name",
    "week_start_date",
    "label_escalation_7d",
    "label_escalation_30d",
    "label_onset_30d",
    "label_onset_90d",
    "label_interstate_30d",
    "label_interstate_onset_30d",
    "label_interstate_onset_90d",
    "organized_violence_quiet_56d",
    "gdelt_event_count_7d",
    "gdelt_event_count_28d",
    "gdelt_event_count_7d_delta",
    "gdelt_avg_goldstein_7d",
    "gdelt_avg_event_tone_7d",
    "gdelt_num_mentions_7d",
    "gdelt_num_articles_7d",
    "gdelt_document_count_7d",
    "gdelt_document_count_28d",
    "gdelt_document_count_7d_delta",
    "gdelt_avg_document_tone_7d",
    "acled_event_count_7d",
    "acled_event_count_7d_delta",
    "acled_fatalities_sum_7d",
    "acled_fatalities_sum_7d_delta",
    "acled_protest_count_7d",
    "acled_protest_count_7d_delta",
    "acled_riot_count_7d",
    "acled_riot_count_7d_delta",
    "acled_violence_against_civilians_count_7d",
    "acled_explosions_remote_violence_count_7d",
    "acled_strategic_developments_count_7d",
    "acled_distinct_actor1_count_7d",
    "acled_distinct_actor2_count_7d",
    "acled_event_count_28d",
    "acled_fatalities_sum_28d",
    "market_oil_price_usd_per_barrel",
    "market_gas_price_index",
    "market_fertilizer_price_index",
    "market_commodity_price_index",
    "food_price_index",
    "food_cereal_price_index",
    "trade_exports_value_usd",
    "trade_imports_value_usd",
    "trade_exports_3m_change_pct",
    "trade_imports_3m_change_pct",
    "shipping_lsci_index",
    "shipping_port_connectivity_index",
    "governance_voice_and_accountability",
    "governance_political_stability",
    "governance_government_effectiveness",
    "governance_regulatory_quality",
    "governance_rule_of_law",
    "governance_control_of_corruption",
    "governance_score",
    "days_to_next_election",
    "days_since_last_election",
    "election_upcoming_30d",
    "election_upcoming_90d",
    "election_recent_30d",
    "election_recent_90d",
    "climate_drought_severity_index",
    "climate_temperature_anomaly_c",
    "climate_precipitation_anomaly_pct",
    "climate_night_lights_anomaly_pct",
    "climate_night_lights_zscore",
    "security_military_expenditure_usd",
    "security_military_expenditure_pct_gdp",
    "security_arms_import_volume_index",
    "ucdp_history_event_count_52w",
    "ucdp_history_best_deaths_52w",
    "ucdp_history_state_based_events_52w",
    "macro_gdp_growth_annual_pct",
    "macro_cpi_yoy",
    "macro_population_total",
    "humanitarian_refugees",
    "humanitarian_asylum_seekers",
    "humanitarian_idps",
    "snapshot_ts_utc",
]


def _empty_country_week_features_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=COUNTRY_WEEK_FEATURE_COLUMNS)


def _max_truth_coverage_end_date(*onset_frames: pd.DataFrame) -> pd.Timestamp | pd.NaT:
    coverage_years: list[int] = []
    for frame in onset_frames:
        if frame.empty or "year" not in frame.columns:
            continue
        years = pd.to_numeric(frame["year"], errors="coerce").dropna().astype(int)
        if not years.empty:
            coverage_years.append(int(years.max()))
    if not coverage_years:
        return pd.NaT
    return pd.Timestamp(year=max(coverage_years), month=12, day=31)


def _metadata_frame(
    frame: pd.DataFrame,
    *,
    country_iso3_column: str = "country_iso3",
    country_name_column: str = "country_name",
    region_name_column: str | None = None,
) -> pd.DataFrame:
    if frame.empty or country_iso3_column not in frame.columns:
        return pd.DataFrame(columns=["country_iso3", "country_name", "region_name"])
    columns = [country_iso3_column]
    if country_name_column in frame.columns:
        columns.append(country_name_column)
    if region_name_column is not None and region_name_column in frame.columns:
        columns.append(region_name_column)
    metadata = frame.loc[frame[country_iso3_column].notna(), columns].copy()
    renamed_columns = {
        country_iso3_column: "country_iso3",
        country_name_column: "country_name",
    }
    if region_name_column is not None:
        renamed_columns[region_name_column] = "region_name"
    metadata = metadata.rename(columns=renamed_columns)
    if "country_name" not in metadata.columns:
        metadata["country_name"] = pd.NA
    if "region_name" not in metadata.columns:
        metadata["region_name"] = pd.NA
    return metadata[["country_iso3", "country_name", "region_name"]]


def _append_country_values(values: list[str | None], frame: pd.DataFrame, column: str) -> None:
    if frame.empty or column not in frame.columns:
        return
    values.extend(frame[column].tolist())


def _infer_panel_start_date(
    *,
    current_week_start: pd.Timestamp,
    ucdp_events: pd.DataFrame,
    wdi_snapshot: pd.DataFrame,
    wgi_snapshot: pd.DataFrame,
    sipri_snapshot: pd.DataFrame,
    unhcr_origin_population: pd.DataFrame,
    gdelt_events: pd.DataFrame,
    gdelt_documents: pd.DataFrame,
    acled_events: pd.DataFrame,
    idea_elections: pd.DataFrame,
    noaa_snapshot: pd.DataFrame,
    nasa_black_marble_snapshot: pd.DataFrame,
    un_comtrade_snapshot: pd.DataFrame,
    unctad_snapshot: pd.DataFrame,
) -> pd.Timestamp:
    candidate_dates: list[pd.Timestamp] = []
    for frame, column in [
        (gdelt_events, "event_date"),
        (gdelt_documents, "document_date"),
        (acled_events, "event_date"),
        (ucdp_events, "event_date_start"),
        (idea_elections, "election_date"),
        (noaa_snapshot, "observation_date"),
        (nasa_black_marble_snapshot, "observation_date"),
        (un_comtrade_snapshot, "observation_date"),
        (unctad_snapshot, "observation_date"),
    ]:
        if frame.empty or column not in frame.columns:
            continue
        observed_dates = pd.to_datetime(frame[column], errors="coerce").dropna()
        if not observed_dates.empty:
            candidate_dates.append(_week_start_from_timestamp(observed_dates.min()))
    for frame, column in [
        (wdi_snapshot, "year"),
        (wgi_snapshot, "year"),
        (sipri_snapshot, "year"),
        (unhcr_origin_population, "year"),
    ]:
        if frame.empty or column not in frame.columns:
            continue
        years = pd.to_numeric(frame[column], errors="coerce").dropna()
        if not years.empty:
            candidate_dates.append(_week_start_from_timestamp(pd.Timestamp(year=int(years.min()), month=1, day=1)))
    if candidate_dates:
        return min(candidate_dates)
    return current_week_start


def build_country_week_features(
    *,
    gdelt_events: pd.DataFrame,
    gdelt_documents: pd.DataFrame,
    acled_events: pd.DataFrame,
    imf_snapshot: pd.DataFrame,
    fao_snapshot: pd.DataFrame,
    wgi_snapshot: pd.DataFrame,
    idea_elections: pd.DataFrame,
    noaa_snapshot: pd.DataFrame,
    sipri_snapshot: pd.DataFrame,
    nasa_black_marble_snapshot: pd.DataFrame,
    un_comtrade_snapshot: pd.DataFrame,
    unctad_snapshot: pd.DataFrame,
    ucdp_events: pd.DataFrame,
    ucdp_interstate_onset: pd.DataFrame,
    ucdp_intrastate_onset: pd.DataFrame,
    wdi_snapshot: pd.DataFrame,
    unhcr_origin_population: pd.DataFrame,
    panel_start_date: pd.Timestamp | str | date | None = None,
    panel_end_date: pd.Timestamp | str | date | None = None,
    snapshot_ts_utc: pd.Timestamp | str,
) -> pd.DataFrame:
    snapshot_ts = _ensure_timestamp(snapshot_ts_utc)
    current_week_start = _week_start_from_timestamp(snapshot_ts)
    snapshot_cutoff_date = snapshot_ts.tz_localize(None).normalize()

    imf = imf_snapshot.copy()
    if not imf.empty:
        imf["observation_date"] = pd.to_datetime(imf["observation_date"], errors="coerce").dt.normalize()
    fao = fao_snapshot.copy()
    if not fao.empty:
        fao["observation_date"] = pd.to_datetime(fao["observation_date"], errors="coerce").dt.normalize()
    ucdp = ucdp_events.copy()
    if not ucdp.empty:
        ucdp["event_date_start"] = pd.to_datetime(ucdp["event_date_start"], errors="coerce").dt.normalize()
        ucdp["week_start_date"] = _week_start_from_series(ucdp["event_date_start"])
        if "conflict_new_id" in ucdp.columns:
            ucdp["conflict_new_id"] = pd.to_numeric(ucdp["conflict_new_id"], errors="coerce").astype("Int64")
    interstate_onset = ucdp_interstate_onset.copy()
    if not interstate_onset.empty:
        interstate_onset["year"] = pd.to_numeric(interstate_onset["year"], errors="coerce").astype("Int64")
        interstate_onset["onset1"] = pd.to_numeric(interstate_onset["onset1"], errors="coerce").fillna(0).astype("Int64")
    intrastate_onset = ucdp_intrastate_onset.copy()
    if not intrastate_onset.empty:
        intrastate_onset["year"] = pd.to_numeric(intrastate_onset["year"], errors="coerce").astype("Int64")
        intrastate_onset["onset1"] = pd.to_numeric(intrastate_onset["onset1"], errors="coerce").fillna(0).astype("Int64")
    wgi = wgi_snapshot.copy()
    if not wgi.empty:
        wgi["year"] = pd.to_numeric(wgi["year"], errors="coerce").astype("Int64")
    noaa = noaa_snapshot.copy()
    if not noaa.empty:
        noaa["observation_date"] = pd.to_datetime(noaa["observation_date"], errors="coerce").dt.normalize()
    sipri = sipri_snapshot.copy()
    if not sipri.empty:
        sipri["year"] = pd.to_numeric(sipri["year"], errors="coerce").astype("Int64")
    nasa_black_marble = nasa_black_marble_snapshot.copy()
    if not nasa_black_marble.empty:
        nasa_black_marble["observation_date"] = pd.to_datetime(nasa_black_marble["observation_date"], errors="coerce").dt.normalize()
    un_comtrade = un_comtrade_snapshot.copy()
    if not un_comtrade.empty:
        un_comtrade["observation_date"] = pd.to_datetime(un_comtrade["observation_date"], errors="coerce").dt.normalize()
    unctad = unctad_snapshot.copy()
    if not unctad.empty:
        unctad["observation_date"] = pd.to_datetime(unctad["observation_date"], errors="coerce").dt.normalize()
    idea = idea_elections.copy()
    if not idea.empty:
        idea["election_date"] = pd.to_datetime(idea["election_date"], errors="coerce").dt.normalize()
    unhcr = unhcr_origin_population.rename(columns={"country_id": "country_iso3"}).copy()
    if not unhcr.empty:
        unhcr["year"] = pd.to_numeric(unhcr["year"], errors="coerce").astype("Int64")
    localized_onsets = localize_ucdp_country_onsets(
        ucdp_events=ucdp,
        interstate_onsets=interstate_onset,
        intrastate_onsets=intrastate_onset,
    )
    onset_truth_cutoff_date = _max_truth_coverage_end_date(interstate_onset, intrastate_onset)
    if not pd.isna(onset_truth_cutoff_date):
        onset_truth_cutoff_date = min(onset_truth_cutoff_date, snapshot_cutoff_date)

    if panel_start_date is None:
        panel_start = _infer_panel_start_date(
            current_week_start=current_week_start,
            ucdp_events=ucdp,
            wdi_snapshot=wdi_snapshot,
            wgi_snapshot=wgi,
            sipri_snapshot=sipri,
            unhcr_origin_population=unhcr,
            gdelt_events=gdelt_events,
            gdelt_documents=gdelt_documents,
            acled_events=acled_events,
            idea_elections=idea,
            noaa_snapshot=noaa,
            nasa_black_marble_snapshot=nasa_black_marble,
            un_comtrade_snapshot=un_comtrade,
            unctad_snapshot=unctad,
        )
    else:
        panel_start = _week_start_from_timestamp(panel_start_date)
    panel_end = current_week_start if panel_end_date is None else _week_start_from_timestamp(panel_end_date)
    if panel_end > current_week_start:
        panel_end = current_week_start
    if panel_end < panel_start:
        raise ValueError("panel_end_date must be on or after panel_start_date")

    metadata_frames = [
        _metadata_frame(wdi_snapshot),
        _metadata_frame(wgi),
        _metadata_frame(idea),
        _metadata_frame(noaa),
        _metadata_frame(sipri),
        _metadata_frame(nasa_black_marble),
        _metadata_frame(un_comtrade),
        _metadata_frame(unctad),
        _metadata_frame(ucdp, region_name_column="region_name"),
        _metadata_frame(unhcr),
    ]
    known_country_values: list[str | None] = []
    _append_country_values(known_country_values, gdelt_events, "country_id")
    _append_country_values(known_country_values, gdelt_documents, "document_country_id")
    _append_country_values(known_country_values, acled_events, "country_iso3")
    for metadata_frame in metadata_frames:
        _append_country_values(known_country_values, metadata_frame, "country_iso3")
    country_dimension = build_country_dimension(known_country_values, metadata_frames=metadata_frames)
    weekly_index = build_weekly_date_index(panel_start, panel_end)
    base_panel = build_country_week_panel(country_dimension, weekly_index)
    if base_panel.empty:
        return _empty_country_week_features_frame()
    panel_week_starts = [pd.Timestamp(value) for value in weekly_index["week_start_date"].tolist()]
    market_lookup = _build_asof_row_lookup(imf, "observation_date", panel_week_starts)
    food_lookup = _build_asof_row_lookup(fao, "observation_date", panel_week_starts)

    results: list[dict[str, object]] = []
    for country_iso3, country_rows in base_panel.groupby("country_iso3", dropna=False):
        country_name = country_rows["country_name"].iloc[0]
        region_values = country_rows["region_name"].dropna()
        region_name = region_values.iloc[0] if not region_values.empty else pd.NA

        country_gdelt_events = gdelt_events.loc[gdelt_events["country_id"] == country_iso3].copy()
        country_gdelt_events["event_date"] = pd.to_datetime(country_gdelt_events["event_date"], errors="coerce").dt.normalize()
        country_gdelt_events = country_gdelt_events.loc[country_gdelt_events["event_date"].notna()].sort_values("event_date").reset_index(drop=True)
        gdelt_event_dates = country_gdelt_events["event_date"].to_numpy(dtype="datetime64[ns]")
        gdelt_goldstein_prefix = _prefix_sum(pd.to_numeric(country_gdelt_events["goldstein_scale"], errors="coerce").fillna(0).to_numpy())
        gdelt_tone_prefix = _prefix_sum(pd.to_numeric(country_gdelt_events["avg_tone"], errors="coerce").fillna(0).to_numpy())
        gdelt_mentions_prefix = _prefix_sum(pd.to_numeric(country_gdelt_events["num_mentions"], errors="coerce").fillna(0).to_numpy())
        gdelt_articles_prefix = _prefix_sum(pd.to_numeric(country_gdelt_events["num_articles"], errors="coerce").fillna(0).to_numpy())

        country_gdelt_documents = gdelt_documents.loc[gdelt_documents["document_country_id"] == country_iso3].copy()
        country_gdelt_documents["document_date"] = pd.to_datetime(country_gdelt_documents["document_date"], errors="coerce").dt.normalize()
        country_gdelt_documents = country_gdelt_documents.loc[country_gdelt_documents["document_date"].notna()].sort_values("document_date").reset_index(drop=True)
        gdelt_document_dates = country_gdelt_documents["document_date"].to_numpy(dtype="datetime64[ns]")
        gdelt_document_tone_prefix = _prefix_sum(pd.to_numeric(country_gdelt_documents["tone_score"], errors="coerce").fillna(0).to_numpy())

        country_acled = acled_events.loc[acled_events["country_iso3"] == country_iso3].copy()
        if not country_acled.empty:
            country_acled["event_date"] = pd.to_datetime(country_acled["event_date"], errors="coerce").dt.normalize()
            country_acled["fatalities"] = pd.to_numeric(country_acled["fatalities"], errors="coerce").fillna(0)
        country_acled = country_acled.loc[country_acled["event_date"].notna()].sort_values("event_date").reset_index(drop=True)
        acled_dates = country_acled["event_date"].to_numpy(dtype="datetime64[ns]")
        acled_fatalities_prefix = _prefix_sum(country_acled.get("fatalities", pd.Series(dtype=float)).fillna(0).to_numpy() if not country_acled.empty else np.array([], dtype=float))
        acled_is_protest_prefix = _prefix_sum((country_acled.get("event_type_slug", pd.Series(dtype="string")) == "protests").astype(int).to_numpy() if not country_acled.empty else np.array([], dtype=float))
        acled_is_riot_prefix = _prefix_sum((country_acled.get("event_type_slug", pd.Series(dtype="string")) == "riots").astype(int).to_numpy() if not country_acled.empty else np.array([], dtype=float))
        acled_is_vac_prefix = _prefix_sum((country_acled.get("event_type_slug", pd.Series(dtype="string")) == "violence_against_civilians").astype(int).to_numpy() if not country_acled.empty else np.array([], dtype=float))
        acled_is_explosion_prefix = _prefix_sum((country_acled.get("event_type_slug", pd.Series(dtype="string")) == "explosions_remote_violence").astype(int).to_numpy() if not country_acled.empty else np.array([], dtype=float))
        acled_is_strategic_prefix = _prefix_sum((country_acled.get("event_type_slug", pd.Series(dtype="string")) == "strategic_developments").astype(int).to_numpy() if not country_acled.empty else np.array([], dtype=float))
        acled_actor1_values = country_acled.get("actor1_name", pd.Series(dtype="string")).astype("string").to_numpy()
        acled_actor2_values = country_acled.get("actor2_name", pd.Series(dtype="string")).astype("string").to_numpy()

        country_ucdp = ucdp.loc[ucdp["country_iso3"] == country_iso3].copy()
        country_ucdp = country_ucdp.loc[country_ucdp["event_date_start"].notna()].sort_values("event_date_start").reset_index(drop=True)
        ucdp_dates = country_ucdp["event_date_start"].to_numpy(dtype="datetime64[ns]")
        ucdp_best_prefix = _prefix_sum(pd.to_numeric(country_ucdp.get("best_fatalities", pd.Series(dtype=float)), errors="coerce").fillna(0).to_numpy())
        ucdp_state_based_prefix = _prefix_sum((pd.to_numeric(country_ucdp.get("type_of_violence", pd.Series(dtype=float)), errors="coerce").fillna(0) == 1).astype(int).to_numpy() if not country_ucdp.empty else np.array([], dtype=float))
        country_localized_onsets = localized_onsets.loc[localized_onsets["country_iso3"] == country_iso3].copy()
        country_localized_onsets = country_localized_onsets.loc[country_localized_onsets["onset_date"].notna()].sort_values("onset_date").reset_index(drop=True)
        onset_dates = country_localized_onsets["onset_date"].to_numpy(dtype="datetime64[ns]")
        onset_interstate_prefix = _prefix_sum((country_localized_onsets.get("onset_type", pd.Series(dtype="string")) == "interstate").astype(int).to_numpy() if not country_localized_onsets.empty else np.array([], dtype=float))
        country_wdi = wdi_snapshot.loc[wdi_snapshot["country_iso3"] == country_iso3].copy()
        country_wgi = wgi.loc[wgi["country_iso3"] == country_iso3].copy()
        country_idea = idea.loc[idea["country_iso3"] == country_iso3].copy()
        country_noaa = noaa.loc[noaa["country_iso3"] == country_iso3].copy()
        country_sipri = sipri.loc[sipri["country_iso3"] == country_iso3].copy()
        country_nasa_black_marble = nasa_black_marble.loc[nasa_black_marble["country_iso3"] == country_iso3].copy()
        country_un_comtrade = un_comtrade.loc[un_comtrade["country_iso3"] == country_iso3].copy()
        country_unctad = unctad.loc[unctad["country_iso3"] == country_iso3].copy()
        country_unhcr = unhcr.loc[unhcr["country_iso3"] == country_iso3].copy()
        country_week_starts = [pd.Timestamp(value) for value in country_rows["week_start_date"].tolist()]
        country_years = [week_start.year for week_start in country_week_starts]
        trade_lookup = _build_asof_row_lookup(country_un_comtrade, "observation_date", country_week_starts)
        shipping_lookup = _build_asof_row_lookup(country_unctad, "observation_date", country_week_starts)
        climate_lookup = _build_asof_row_lookup(country_noaa, "observation_date", country_week_starts)
        night_lights_lookup = _build_asof_row_lookup(country_nasa_black_marble, "observation_date", country_week_starts)
        macro_lookup = _build_latest_year_row_lookup(country_wdi, country_years)
        governance_lookup = _build_latest_year_row_lookup(country_wgi, country_years)
        security_lookup = _build_latest_year_row_lookup(country_sipri, country_years)
        humanitarian_lookup = _build_latest_year_row_lookup(country_unhcr, country_years)
        election_lookup = _build_election_date_lookup(country_idea, country_week_starts)

        for week_start in country_week_starts:
            trailing_7d_start = week_start - pd.Timedelta(days=6)
            trailing_28d_start = week_start - pd.Timedelta(days=27)
            trailing_56d_start = week_start - pd.Timedelta(days=55)
            future_7d_end = week_start + pd.Timedelta(days=7)
            future_30d_end = week_start + pd.Timedelta(days=30)
            future_90d_end = week_start + pd.Timedelta(days=90)
            lookback_180d_start = week_start - pd.Timedelta(days=180)
            lookback_52w_start = week_start - pd.Timedelta(days=364)
            future_7d_known = future_7d_end <= snapshot_cutoff_date
            future_30d_known = future_30d_end <= snapshot_cutoff_date
            future_90d_known = future_90d_end <= snapshot_cutoff_date
            onset_30d_known = not pd.isna(onset_truth_cutoff_date) and future_30d_end <= onset_truth_cutoff_date
            onset_90d_known = not pd.isna(onset_truth_cutoff_date) and future_90d_end <= onset_truth_cutoff_date

            gdelt_event_left_7d, gdelt_event_right_7d = _window_bounds(gdelt_event_dates, trailing_7d_start, week_start)
            gdelt_event_left_28d, gdelt_event_right_28d = _window_bounds(gdelt_event_dates, trailing_28d_start, week_start)
            gdelt_document_left_7d, gdelt_document_right_7d = _window_bounds(gdelt_document_dates, trailing_7d_start, week_start)
            gdelt_document_left_28d, gdelt_document_right_28d = _window_bounds(gdelt_document_dates, trailing_28d_start, week_start)
            acled_left_7d, acled_right_7d = _window_bounds(acled_dates, trailing_7d_start, week_start)
            acled_left_28d, acled_right_28d = _window_bounds(acled_dates, trailing_28d_start, week_start)
            ucdp_history_left, ucdp_history_right = _window_bounds(ucdp_dates, lookback_52w_start, week_start)
            ucdp_future_left_7d, ucdp_future_right_7d = _window_bounds(ucdp_dates, week_start + pd.Timedelta(days=1), future_7d_end)
            ucdp_future_left_30d, ucdp_future_right_30d = _window_bounds(ucdp_dates, week_start + pd.Timedelta(days=1), future_30d_end)
            ucdp_future_left_90d, ucdp_future_right_90d = _window_bounds(ucdp_dates, week_start + pd.Timedelta(days=1), future_90d_end)
            ucdp_lookback_left_180d, ucdp_lookback_right_180d = _window_bounds(ucdp_dates, lookback_180d_start, week_start)
            ucdp_lookback_left_56d, ucdp_lookback_right_56d = _window_bounds(ucdp_dates, trailing_56d_start, week_start)
            onset_left_30d, onset_right_30d = _window_bounds(onset_dates, week_start + pd.Timedelta(days=1), future_30d_end)
            onset_left_90d, onset_right_90d = _window_bounds(onset_dates, week_start + pd.Timedelta(days=1), future_90d_end)
            market_row = market_lookup.get(week_start, {})
            food_row = food_lookup.get(week_start, {})
            trade_row = trade_lookup.get(week_start, {})
            shipping_row = shipping_lookup.get(week_start, {})
            macro_row = macro_lookup.get(week_start.year, {})
            governance_row = governance_lookup.get(week_start.year, {})
            climate_row = climate_lookup.get(week_start, {})
            security_row = security_lookup.get(week_start.year, {})
            night_lights_row = night_lights_lookup.get(week_start, {})
            humanitarian_row = humanitarian_lookup.get(week_start.year, {})
            next_election_date, last_election_date = election_lookup.get(week_start, (pd.NaT, pd.NaT))

            days_to_next_election = _to_nullable_days(next_election_date - week_start if not pd.isna(next_election_date) else None)
            days_since_last_election = _to_nullable_days(week_start - last_election_date if not pd.isna(last_election_date) else None)

            future_7d_best_deaths = _window_sum(ucdp_best_prefix, ucdp_future_left_7d, ucdp_future_right_7d)
            future_30d_best_deaths = _window_sum(ucdp_best_prefix, ucdp_future_left_30d, ucdp_future_right_30d)
            future_90d_best_deaths = _window_sum(ucdp_best_prefix, ucdp_future_left_90d, ucdp_future_right_90d)
            lookback_180d_best_deaths = _window_sum(ucdp_best_prefix, ucdp_lookback_left_180d, ucdp_lookback_right_180d)
            lookback_56d_best_deaths = _window_sum(ucdp_best_prefix, ucdp_lookback_left_56d, ucdp_lookback_right_56d)
            gdelt_event_count_7d = gdelt_event_right_7d - gdelt_event_left_7d
            gdelt_event_count_28d = gdelt_event_right_28d - gdelt_event_left_28d
            gdelt_document_count_7d = gdelt_document_right_7d - gdelt_document_left_7d
            gdelt_document_count_28d = gdelt_document_right_28d - gdelt_document_left_28d
            acled_event_count_7d = acled_right_7d - acled_left_7d
            acled_event_count_28d = acled_right_28d - acled_left_28d
            acled_fatalities_sum_7d = _window_sum(acled_fatalities_prefix, acled_left_7d, acled_right_7d)
            acled_fatalities_sum_28d = _window_sum(acled_fatalities_prefix, acled_left_28d, acled_right_28d)
            acled_protest_count_7d = int(_window_sum(acled_is_protest_prefix, acled_left_7d, acled_right_7d))
            acled_protest_count_28d = int(_window_sum(acled_is_protest_prefix, acled_left_28d, acled_right_28d))
            acled_riot_count_7d = int(_window_sum(acled_is_riot_prefix, acled_left_7d, acled_right_7d))
            acled_riot_count_28d = int(_window_sum(acled_is_riot_prefix, acled_left_28d, acled_right_28d))
            onset_count_30d = onset_right_30d - onset_left_30d
            onset_count_90d = onset_right_90d - onset_left_90d
            interstate_onset_count_30d = int(_window_sum(onset_interstate_prefix, onset_left_30d, onset_right_30d))
            interstate_onset_count_90d = int(_window_sum(onset_interstate_prefix, onset_left_90d, onset_right_90d))

            results.append(
                {
                    "country_iso3": country_iso3,
                    "country_name": country_name,
                    "region_name": region_name,
                    "week_start_date": week_start.date(),
                    "label_escalation_7d": _as_known_int_or_na(future_7d_best_deaths > 0, is_known=future_7d_known),
                    "label_escalation_30d": _as_known_int_or_na(future_30d_best_deaths > 0, is_known=future_30d_known),
                    "label_onset_30d": _as_known_int_or_na(
                        onset_count_30d > 0,
                        is_known=onset_30d_known,
                    ),
                    "label_onset_90d": _as_known_int_or_na(
                        onset_count_90d > 0,
                        is_known=onset_90d_known,
                    ),
                    "label_interstate_30d": _as_known_int_or_na(
                        interstate_onset_count_30d > 0,
                        is_known=onset_30d_known,
                    ),
                    "label_interstate_onset_30d": _as_known_int_or_na(
                        interstate_onset_count_30d > 0,
                        is_known=onset_30d_known,
                    ),
                    "label_interstate_onset_90d": _as_known_int_or_na(
                        interstate_onset_count_90d > 0,
                        is_known=onset_90d_known,
                    ),
                    "organized_violence_quiet_56d": int(lookback_56d_best_deaths == 0),
                    "gdelt_event_count_7d": gdelt_event_count_7d,
                    "gdelt_event_count_28d": gdelt_event_count_28d,
                    "gdelt_event_count_7d_delta": _delta_from_short_long(gdelt_event_count_7d, gdelt_event_count_28d, 4),
                    "gdelt_avg_goldstein_7d": _window_mean(gdelt_goldstein_prefix, gdelt_event_left_7d, gdelt_event_right_7d),
                    "gdelt_avg_event_tone_7d": _window_mean(gdelt_tone_prefix, gdelt_event_left_7d, gdelt_event_right_7d),
                    "gdelt_num_mentions_7d": _window_sum(gdelt_mentions_prefix, gdelt_event_left_7d, gdelt_event_right_7d),
                    "gdelt_num_articles_7d": _window_sum(gdelt_articles_prefix, gdelt_event_left_7d, gdelt_event_right_7d),
                    "gdelt_document_count_7d": gdelt_document_count_7d,
                    "gdelt_document_count_28d": gdelt_document_count_28d,
                    "gdelt_document_count_7d_delta": _delta_from_short_long(
                        gdelt_document_count_7d,
                        gdelt_document_count_28d,
                        4,
                    ),
                    "gdelt_avg_document_tone_7d": _window_mean(
                        gdelt_document_tone_prefix,
                        gdelt_document_left_7d,
                        gdelt_document_right_7d,
                    ),
                    "acled_event_count_7d": acled_event_count_7d,
                    "acled_event_count_7d_delta": _delta_from_short_long(acled_event_count_7d, acled_event_count_28d, 4),
                    "acled_fatalities_sum_7d": acled_fatalities_sum_7d,
                    "acled_fatalities_sum_7d_delta": _delta_from_short_long(
                        acled_fatalities_sum_7d,
                        acled_fatalities_sum_28d,
                        4,
                    ),
                    "acled_protest_count_7d": acled_protest_count_7d,
                    "acled_protest_count_7d_delta": _delta_from_short_long(acled_protest_count_7d, acled_protest_count_28d, 4),
                    "acled_riot_count_7d": acled_riot_count_7d,
                    "acled_riot_count_7d_delta": _delta_from_short_long(acled_riot_count_7d, acled_riot_count_28d, 4),
                    "acled_violence_against_civilians_count_7d": int(_window_sum(acled_is_vac_prefix, acled_left_7d, acled_right_7d)),
                    "acled_explosions_remote_violence_count_7d": int(
                        _window_sum(acled_is_explosion_prefix, acled_left_7d, acled_right_7d)
                    ),
                    "acled_strategic_developments_count_7d": int(
                        _window_sum(acled_is_strategic_prefix, acled_left_7d, acled_right_7d)
                    ),
                    "acled_distinct_actor1_count_7d": _window_unique_count(acled_actor1_values, acled_left_7d, acled_right_7d),
                    "acled_distinct_actor2_count_7d": _window_unique_count(acled_actor2_values, acled_left_7d, acled_right_7d),
                    "acled_event_count_28d": acled_event_count_28d,
                    "acled_fatalities_sum_28d": acled_fatalities_sum_28d,
                    "market_oil_price_usd_per_barrel": market_row.get("market_oil_price_usd_per_barrel"),
                    "market_gas_price_index": market_row.get("market_gas_price_index"),
                    "market_fertilizer_price_index": market_row.get("market_fertilizer_price_index"),
                    "market_commodity_price_index": market_row.get("market_commodity_price_index"),
                    "food_price_index": food_row.get("food_price_index"),
                    "food_cereal_price_index": food_row.get("food_cereal_price_index"),
                    "trade_exports_value_usd": trade_row.get("trade_exports_value_usd"),
                    "trade_imports_value_usd": trade_row.get("trade_imports_value_usd"),
                    "trade_exports_3m_change_pct": trade_row.get("trade_exports_3m_change_pct"),
                    "trade_imports_3m_change_pct": trade_row.get("trade_imports_3m_change_pct"),
                    "shipping_lsci_index": shipping_row.get("shipping_lsci_index"),
                    "shipping_port_connectivity_index": shipping_row.get("shipping_port_connectivity_index"),
                    "governance_voice_and_accountability": governance_row.get("governance_voice_and_accountability"),
                    "governance_political_stability": governance_row.get("governance_political_stability"),
                    "governance_government_effectiveness": governance_row.get("governance_government_effectiveness"),
                    "governance_regulatory_quality": governance_row.get("governance_regulatory_quality"),
                    "governance_rule_of_law": governance_row.get("governance_rule_of_law"),
                    "governance_control_of_corruption": governance_row.get("governance_control_of_corruption"),
                    "governance_score": governance_row.get("governance_score"),
                    "days_to_next_election": days_to_next_election,
                    "days_since_last_election": days_since_last_election,
                    "election_upcoming_30d": _within_days(days_to_next_election, 30),
                    "election_upcoming_90d": _within_days(days_to_next_election, 90),
                    "election_recent_30d": _within_days(days_since_last_election, 30),
                    "election_recent_90d": _within_days(days_since_last_election, 90),
                    "climate_drought_severity_index": climate_row.get("climate_drought_severity_index"),
                    "climate_temperature_anomaly_c": climate_row.get("climate_temperature_anomaly_c"),
                    "climate_precipitation_anomaly_pct": climate_row.get("climate_precipitation_anomaly_pct"),
                    "climate_night_lights_anomaly_pct": night_lights_row.get("climate_night_lights_anomaly_pct"),
                    "climate_night_lights_zscore": night_lights_row.get("climate_night_lights_zscore"),
                    "security_military_expenditure_usd": security_row.get("security_military_expenditure_usd"),
                    "security_military_expenditure_pct_gdp": security_row.get("security_military_expenditure_pct_gdp"),
                    "security_arms_import_volume_index": security_row.get("security_arms_import_volume_index"),
                    "ucdp_history_event_count_52w": int(ucdp_history_right - ucdp_history_left),
                    "ucdp_history_best_deaths_52w": _window_sum(ucdp_best_prefix, ucdp_history_left, ucdp_history_right),
                    "ucdp_history_state_based_events_52w": int(
                        _window_sum(ucdp_state_based_prefix, ucdp_history_left, ucdp_history_right)
                    ),
                    "macro_gdp_growth_annual_pct": macro_row.get("macro_gdp_growth_annual_pct"),
                    "macro_cpi_yoy": macro_row.get("macro_cpi_yoy"),
                    "macro_population_total": macro_row.get("macro_population_total"),
                    "humanitarian_refugees": humanitarian_row.get("refugees"),
                    "humanitarian_asylum_seekers": humanitarian_row.get("asylum_seekers"),
                    "humanitarian_idps": humanitarian_row.get("idps"),
                    "snapshot_ts_utc": snapshot_ts,
                }
            )

    gold = pd.DataFrame(results, columns=COUNTRY_WEEK_FEATURE_COLUMNS).sort_values(
        by=["country_iso3", "week_start_date"]
    ).reset_index(drop=True)
    gold["country_name"] = gold["country_name"].astype("string")
    gold["region_name"] = gold["region_name"].astype("string")
    for column in [
        "label_escalation_7d",
        "label_escalation_30d",
        "label_onset_30d",
        "label_onset_90d",
        "label_interstate_30d",
        "label_interstate_onset_30d",
        "label_interstate_onset_90d",
        "organized_violence_quiet_56d",
        "gdelt_event_count_28d",
        "gdelt_document_count_28d",
        "acled_event_count_7d",
        "acled_protest_count_7d",
        "acled_riot_count_7d",
        "acled_violence_against_civilians_count_7d",
        "acled_explosions_remote_violence_count_7d",
        "acled_strategic_developments_count_7d",
        "acled_distinct_actor1_count_7d",
        "acled_distinct_actor2_count_7d",
        "acled_event_count_28d",
        "ucdp_history_event_count_52w",
        "ucdp_history_state_based_events_52w",
        "days_to_next_election",
        "days_since_last_election",
        "election_upcoming_30d",
        "election_upcoming_90d",
        "election_recent_30d",
        "election_recent_90d",
    ]:
        gold[column] = gold[column].astype("Int64")
    return gold
