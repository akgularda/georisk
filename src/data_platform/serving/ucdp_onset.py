from __future__ import annotations

import re

import pandas as pd


def _parse_conflict_ids(value: object) -> set[int]:
    if value is None or pd.isna(value):
        return set()
    return {int(token) for token in re.findall(r"\d+", str(value))}


def _eligible_onset_rows(frame: pd.DataFrame, onset_type: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "country_iso3",
                "country_name",
                "year",
                "onset1",
                "onset20",
                "conflict_ids",
                "onset_type",
            ]
        )
    eligible = frame.loc[
        frame["country_iso3"].notna()
        & frame["year"].notna()
        & (pd.to_numeric(frame["onset1"], errors="coerce").fillna(0) > 0)
    ].copy()
    eligible["onset_type"] = onset_type
    return eligible


def localize_ucdp_country_onsets(
    *,
    ucdp_events: pd.DataFrame,
    interstate_onsets: pd.DataFrame,
    intrastate_onsets: pd.DataFrame,
) -> pd.DataFrame:
    if ucdp_events.empty:
        return pd.DataFrame(
            columns=[
                "country_iso3",
                "country_name",
                "onset_type",
                "onset_year",
                "onset_date",
                "onset20",
                "conflict_ids",
                "localization_method",
            ]
        )

    events = ucdp_events.copy()
    events["event_date_start"] = pd.to_datetime(events["event_date_start"], errors="coerce").dt.normalize()
    if "year" in events.columns:
        events["year"] = pd.to_numeric(events["year"], errors="coerce").astype("Int64")
    else:
        events["year"] = events["event_date_start"].dt.year.astype("Int64")
    if "conflict_new_id" in events.columns:
        events["conflict_new_id"] = pd.to_numeric(events["conflict_new_id"], errors="coerce").astype("Int64")
    else:
        events["conflict_new_id"] = pd.Series(pd.array([pd.NA] * len(events), dtype="Int64"), index=events.index)

    onset_frames = [
        frame
        for frame in [
            _eligible_onset_rows(interstate_onsets, "interstate"),
            _eligible_onset_rows(intrastate_onsets, "intrastate"),
        ]
        if not frame.empty
    ]
    if not onset_frames:
        return pd.DataFrame(
            columns=[
                "country_iso3",
                "country_name",
                "onset_type",
                "onset_year",
                "onset_date",
                "onset20",
                "conflict_ids",
                "localization_method",
            ]
        )
    onset_rows = pd.concat(onset_frames, ignore_index=True)

    records: list[dict[str, object]] = []
    for _, onset_row in onset_rows.iterrows():
        country_iso3 = onset_row["country_iso3"]
        onset_year = int(onset_row["year"])
        country_events = events.loc[
            (events["country_iso3"] == country_iso3)
            & (events["year"] == onset_year)
            & events["event_date_start"].notna()
        ].copy()
        candidate_events = pd.DataFrame(columns=country_events.columns)
        localization_method = pd.NA
        conflict_ids = onset_row.get("conflict_ids")
        parsed_conflict_ids = _parse_conflict_ids(conflict_ids)

        if parsed_conflict_ids:
            candidate_events = country_events.loc[country_events["conflict_new_id"].isin(parsed_conflict_ids)].copy()
            if not candidate_events.empty:
                localization_method = "conflict_id_match"
        if candidate_events.empty:
            candidate_events = country_events
            if not candidate_events.empty:
                localization_method = "country_year_fallback"
        if candidate_events.empty:
            continue

        onset20_value = pd.to_numeric(onset_row.get("onset20"), errors="coerce")
        records.append(
            {
                "country_iso3": country_iso3,
                "country_name": onset_row.get("country_name"),
                "onset_type": onset_row["onset_type"],
                "onset_year": onset_year,
                "onset_date": candidate_events["event_date_start"].min(),
                "onset20": 0 if pd.isna(onset20_value) else int(onset20_value),
                "conflict_ids": conflict_ids,
                "localization_method": localization_method,
            }
        )

    if not records:
        return pd.DataFrame(
            columns=[
                "country_iso3",
                "country_name",
                "onset_type",
                "onset_year",
                "onset_date",
                "onset20",
                "conflict_ids",
                "localization_method",
            ]
        )
    return pd.DataFrame.from_records(records).sort_values(
        ["country_iso3", "onset_date", "onset_type"]
    ).reset_index(drop=True)
