"""Zoho OAuth state in `configuration_data.oauth_clients`: list of client bundles, tokens on same entry."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.hrms.zoho_people.regions import normalize_region

OAUTH_CLIENTS_KEY = "oauth_clients"


def resolve_active_oauth_entry(cfg: dict[str, Any]) -> dict[str, Any]:
    clients = cfg.get(OAUTH_CLIENTS_KEY)
    if isinstance(clients, list) and clients:
        last = clients[-1]
        if isinstance(last, dict) and last.get("client_id"):
            return last
    cid, sec = cfg.get("client_id"), cfg.get("client_secret")
    if cid and sec is not None and str(sec) != "":
        return {
            "client_id": str(cid),
            "client_secret": str(sec),
            "redirect_uri": str(cfg.get("redirect_uri", "")),
            "region": normalize_region(str(cfg.get("region", "com"))),
        }
    raise ValueError("Missing oauth_clients or client credentials in configuration_data")


def resolve_oauth_credentials(cfg: dict[str, Any]) -> tuple[str, str]:
    e = resolve_active_oauth_entry(cfg)
    return str(e["client_id"]), str(e["client_secret"])


def resolve_redirect_uri(cfg: dict[str, Any]) -> str:
    e = resolve_active_oauth_entry(cfg)
    u = e.get("redirect_uri")
    if not u:
        raise ValueError("Missing redirect_uri on active oauth_clients entry")
    return str(u)


def resolve_region(cfg: dict[str, Any]) -> str:
    e = resolve_active_oauth_entry(cfg)
    return normalize_region(str(e.get("region") or "com"))


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        return cfg.get("access_token")
    return e.get("access_token") or cfg.get("access_token")


def resolve_refresh_token(cfg: dict[str, Any]) -> str | None:
    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        return cfg.get("refresh_token")
    return e.get("refresh_token") or cfg.get("refresh_token")


def access_token_expires_raw(cfg: dict[str, Any]) -> str | None:
    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        return cfg.get("access_token_expires_at")
    return e.get("access_token_expires_at") or cfg.get("access_token_expires_at")


def has_access_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_access_token(cfg))
