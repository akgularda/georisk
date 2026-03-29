from __future__ import annotations

import io
import ssl
from urllib.request import urlopen

import pandas as pd


def _build_ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except ImportError:  # pragma: no cover - environment dependent
        return None
    return ssl.create_default_context(cafile=certifi.where())


def fetch_ucdp_onset_csv(download_url: str) -> str:
    context = _build_ssl_context()
    with urlopen(download_url, timeout=180, context=context) as response:
        return response.read().decode("utf-8")


def parse_ucdp_onset_csv(payload: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(payload))
