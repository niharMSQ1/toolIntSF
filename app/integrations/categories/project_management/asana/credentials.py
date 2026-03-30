"""Resolve Asana credentials from tool_integrations.configuration_data."""

from __future__ import annotations

from typing import Any


def resolve_bearer_token(cfg: dict[str, Any]) -> str | None:
    """
    PAT (`personal_access_token`) or OAuth `access_token` — both use
    Authorization: Bearer (https://developers.asana.com/docs/authentication).
    """
    for key in ("personal_access_token", "access_token"):
        t = cfg.get(key)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_bearer_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_bearer_token(cfg))


def resolve_oauth_credentials(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id")
    sec = cfg.get("client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id in configuration_data (Asana OAuth app).")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret in configuration_data.")
    return str(cid).strip(), str(sec).strip()


def resolve_redirect_uri(cfg: dict[str, Any]) -> str:
    u = cfg.get("redirect_uri")
    if not u or not str(u).strip():
        raise ValueError("Missing redirect_uri in configuration_data (must match Asana app callback URL).")
    return str(u).strip()


def resolve_refresh_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("refresh_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def uses_personal_access_token(cfg: dict[str, Any]) -> bool:
    t = cfg.get("personal_access_token")
    return bool(t and str(t).strip())
