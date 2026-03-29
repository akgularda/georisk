from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Iterable
from urllib.request import urlopen

import pandas as pd

from src.data_platform.schemas import GDELTLastUpdate

GDELT_EXPORT_COLUMN_NAMES = [
    "global_event_id",
    "sql_date",
    "month_year",
    "year",
    "fraction_date",
    "actor1_code",
    "actor1_name",
    "actor1_country_code",
    "actor1_known_group_code",
    "actor1_ethnic_code",
    "actor1_religion1_code",
    "actor1_religion2_code",
    "actor1_type1_code",
    "actor1_type2_code",
    "actor1_type3_code",
    "actor2_code",
    "actor2_name",
    "actor2_country_code",
    "actor2_known_group_code",
    "actor2_ethnic_code",
    "actor2_religion1_code",
    "actor2_religion2_code",
    "actor2_type1_code",
    "actor2_type2_code",
    "actor2_type3_code",
    "is_root_event",
    "event_code",
    "event_base_code",
    "event_root_code",
    "quad_class",
    "goldstein_scale",
    "num_mentions",
    "num_sources",
    "num_articles",
    "avg_tone",
    "actor1_geo_type",
    "actor1_geo_full_name",
    "actor1_geo_country_code",
    "actor1_geo_adm1_code",
    "actor1_geo_adm2_code",
    "actor1_geo_lat",
    "actor1_geo_long",
    "actor1_geo_feature_id",
    "actor2_geo_type",
    "actor2_geo_full_name",
    "actor2_geo_country_code",
    "actor2_geo_adm1_code",
    "actor2_geo_adm2_code",
    "actor2_geo_lat",
    "actor2_geo_long",
    "actor2_geo_feature_id",
    "action_geo_type",
    "action_geo_full_name",
    "action_geo_country_code",
    "action_geo_adm1_code",
    "action_geo_adm2_code",
    "action_geo_lat",
    "action_geo_long",
    "action_geo_feature_id",
    "date_added",
    "source_url",
]

GDELT_GKG_COLUMN_NAMES = [
    "gkg_record_id",
    "date",
    "source_collection_identifier",
    "source_common_name",
    "document_identifier",
    "counts",
    "v2_counts",
    "themes",
    "v2_themes",
    "locations",
    "v2_locations",
    "persons",
    "v2_persons",
    "organizations",
    "v2_organizations",
    "v2_tone",
    "dates",
    "gcam",
    "sharing_image",
    "related_images",
    "social_image_embeds",
    "social_video_embeds",
    "quotations",
    "all_names",
    "amounts",
    "translation_info",
    "extras",
]


def parse_gdelt_lastupdate(text: str) -> GDELTLastUpdate:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    export_size, export_md5, export_url = lines[0].split()
    mentions_size, mentions_md5, mentions_url = lines[1].split()
    gkg_size, gkg_md5, gkg_url = lines[2].split()
    return GDELTLastUpdate(
        export_size_bytes=int(export_size),
        export_md5=export_md5,
        export_url=export_url,
        mentions_size_bytes=int(mentions_size),
        mentions_md5=mentions_md5,
        mentions_url=mentions_url,
        gkg_size_bytes=int(gkg_size),
        gkg_md5=gkg_md5,
        gkg_url=gkg_url,
    )


def select_recent_file_urls(masterfile_text: str, suffix: str, limit: int) -> list[str]:
    matched = [line.split()[-1] for line in masterfile_text.splitlines() if line.strip().endswith(suffix)]
    return matched[-limit:]


def fetch_text(url: str) -> str:
    return urlopen(url, timeout=60).read().decode("utf-8")


def fetch_zip_lines(url: str) -> list[str]:
    data = urlopen(url, timeout=120).read()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        member_name = archive.namelist()[0]
        return archive.read(member_name).decode("utf-8", errors="replace").splitlines()


def parse_gdelt_export_lines(lines: Iterable[str]) -> pd.DataFrame:
    frame = pd.read_csv(
        io.StringIO("\n".join(lines)),
        sep="\t",
        header=None,
        names=GDELT_EXPORT_COLUMN_NAMES,
        dtype=str,
    )
    return frame


def parse_gdelt_gkg_lines(lines: Iterable[str]) -> pd.DataFrame:
    frame = pd.read_csv(
        io.StringIO("\n".join(lines)),
        sep="\t",
        header=None,
        names=GDELT_GKG_COLUMN_NAMES,
        dtype=str,
    )
    return frame


def load_snapshot_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")
