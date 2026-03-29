"""Sysdig regional API base URL + API token (Bearer)."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.sysdig_secure.constants import DEFAULT_API_BASE_URL


def resolve_api_token(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("api_token") or cfg.get("sysdig_api_token") or cfg.get("token")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_api_base_url(cfg: dict[str, Any]) -> str:
    """Regional API origin, e.g. ``https://api.us1.sysdig.com`` or on-prem ``https://api.sysdig.example.com``."""
    v = cfg.get("api_base_url") or cfg.get("sysdig_api_base_url") or cfg.get("sdc_url")
    if v and str(v).strip():
        return str(v).strip().rstrip("/")
    return DEFAULT_API_BASE_URL


def resolve_verify_tls(cfg: dict[str, Any]) -> bool:
    v = cfg.get("verify_tls")
    if v is None:
        return True
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y")


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    return bool(resolve_api_token(cfg)) and bool(resolve_api_base_url(cfg))


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg)
