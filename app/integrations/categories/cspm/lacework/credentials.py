"""Lacework account subdomain + API key id + secret (see Fortinet / Lacework API docs)."""

from __future__ import annotations

from typing import Any


def resolve_account_name(cfg: dict[str, Any]) -> str | None:
    """Subdomain only, e.g. `mycompany` for `https://mycompany.lacework.net`."""
    v = cfg.get("account") or cfg.get("lacework_account") or cfg.get("account_name")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_api_base_url(cfg: dict[str, Any]) -> str:
    """HTTPS origin without trailing path, e.g. `https://mycompany.lacework.net`."""
    full = cfg.get("api_base_url") or cfg.get("lacework_api_base_url")
    if full and str(full).strip():
        u = str(full).strip().rstrip("/")
        if "/api" in u:
            # allow mistaken paste of .../api/v2 — strip to origin
            idx = u.find("/api")
            u = u[:idx].rstrip("/")
        return u
    acc = resolve_account_name(cfg)
    if not acc:
        return ""
    return f"https://{acc}.lacework.net".rstrip("/")


def resolve_key_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("key_id") or cfg.get("api_key_id") or cfg.get("lacework_key_id")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_secret(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("secret") or cfg.get("api_secret") or cfg.get("lacework_secret")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    return bool(resolve_api_base_url(cfg)) and bool(resolve_key_id(cfg)) and bool(resolve_secret(cfg))


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg)
