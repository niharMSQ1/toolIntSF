"""Orca API token + regional API host."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.orca_security.constants import DEFAULT_API_HOST


def resolve_api_token(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("api_token") or cfg.get("orca_api_token")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_api_host(cfg: dict[str, Any]) -> str:
    h = cfg.get("api_host") or cfg.get("orca_api_host")
    if h and str(h).strip():
        return str(h).strip().rstrip("/")
    return DEFAULT_API_HOST


def resolve_api_base_url(cfg: dict[str, Any]) -> str:
    """HTTPS base including `/api` suffix (Cortex XSOAR: `https://{api_host}/api`)."""
    full = cfg.get("api_base_url") or cfg.get("orca_api_base_url")
    if full and str(full).strip():
        return str(full).strip().rstrip("/")
    host = resolve_api_host(cfg)
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"https://{host}/api".rstrip("/")


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    return bool(resolve_api_token(cfg)) and bool(resolve_api_base_url(cfg))


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg)
