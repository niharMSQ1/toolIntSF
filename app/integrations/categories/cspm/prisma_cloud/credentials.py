"""Resolve and validate Prisma Cloud REST configuration (CSPM)."""

from __future__ import annotations

import re
from typing import Any

_HTTPS_URL = re.compile(r"^https://[a-zA-Z0-9_.-]+(:\d+)?(/.*)?$")


def resolve_api_base_url(cfg: dict[str, Any]) -> str:
    """Tenant API base URL, e.g. https://api.prismacloud.io (must match console cluster)."""
    u = cfg.get("api_base_url") or cfg.get("prisma_api_url") or ""
    return str(u).strip().rstrip("/")


def resolve_access_key_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("access_key_id") or cfg.get("username")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_secret_key(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("secret_key") or cfg.get("password")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    base = resolve_api_base_url(cfg)
    if not base or not _HTTPS_URL.match(base):
        return False
    if not resolve_access_key_id(cfg) or not resolve_secret_key(cfg):
        return False
    return True


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg)
