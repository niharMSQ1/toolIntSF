"""Microsoft national clouds: commercial (worldwide) vs GCC High (US sovereign)."""

from __future__ import annotations

from enum import Enum


class NationalCloud(str, Enum):
    COMMERCIAL = "commercial"
    GCC_HIGH = "gcc_high"


def parse_national_cloud(raw: str | None) -> NationalCloud:
    if not raw or not str(raw).strip():
        return NationalCloud.COMMERCIAL
    s = str(raw).strip().lower()
    if s in ("gcc_high", "gcchigh", "gcc-high"):
        return NationalCloud.GCC_HIGH
    return NationalCloud.COMMERCIAL


def login_authority_host(cloud: NationalCloud) -> str:
    if cloud == NationalCloud.GCC_HIGH:
        return "https://login.microsoftonline.us"
    return "https://login.microsoftonline.com"


def default_graph_base_url(cloud: NationalCloud) -> str:
    if cloud == NationalCloud.GCC_HIGH:
        return "https://graph.microsoft.us/v1.0"
    return "https://graph.microsoft.com/v1.0"
