from __future__ import annotations

import io
import zipfile
from urllib.request import urlopen

import pandas as pd


def fetch_ucdp_ged_zip(download_url: str) -> bytes:
    return urlopen(download_url, timeout=180).read()


def _coerce_object_columns_to_string(frame: pd.DataFrame) -> pd.DataFrame:
    object_columns = frame.select_dtypes(include=["object"]).columns.tolist()
    if not object_columns:
        return frame

    normalized = frame.copy()
    for column in object_columns:
        normalized[column] = normalized[column].astype("string")
    return normalized


def parse_ucdp_ged_zip(payload: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        member_name = next((name for name in archive.namelist() if name.lower().endswith(".csv")), archive.namelist()[0])
        frame = pd.read_csv(archive.open(member_name), low_memory=False)
    return _coerce_object_columns_to_string(frame)


def parse_ucdp_ged_csv(payload: str) -> pd.DataFrame:
    frame = pd.read_csv(io.StringIO(payload), low_memory=False)
    return _coerce_object_columns_to_string(frame)
