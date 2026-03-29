"""Aqua CSP self-hosted: console base URL + login id + password."""

from __future__ import annotations

from typing import Any


def resolve_api_base_url(cfg: dict[str, Any]) -> str:
    """Origin of the Aqua console, e.g. `https://aqua.example.com:8443` (no `/api` suffix)."""
    v = cfg.get("api_base_url") or cfg.get("aqua_api_base_url") or cfg.get("console_url")
    if v is None or not str(v).strip():
        return ""
    u = str(v).strip().rstrip("/")
    if "/api/" in u:
        idx = u.lower().find("/api/")
        u = u[:idx].rstrip("/")
    return u


def resolve_login_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("login_id") or cfg.get("id") or cfg.get("username") or cfg.get("aqua_username")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_password(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("password") or cfg.get("aqua_password")
    if v is None or not str(v).strip():
        return None
    return str(v)


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    return bool(resolve_api_base_url(cfg)) and bool(resolve_login_id(cfg)) and bool(resolve_password(cfg))


def resolve_verify_tls(cfg: dict[str, Any]) -> bool:
    v = cfg.get("verify_tls")
    if v is None:
        return True
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y")


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg)
