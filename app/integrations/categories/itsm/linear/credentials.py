"""Resolve Linear OAuth and selection data from tool_integrations.configuration_data."""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.integrations.categories.itsm.linear.constants import LINEAR_GRAPHQL_URL


def resolve_oauth_credentials(cfg: dict[str, Any]) -> tuple[str, str]:
    settings = get_settings()
    cid = cfg.get("client_id") or settings.linear_client_id
    sec = cfg.get("client_secret") or settings.linear_client_secret
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id in configuration_data (Linear OAuth app).")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret in configuration_data.")
    return str(cid).strip(), str(sec).strip()


def resolve_redirect_uri(cfg: dict[str, Any]) -> str:
    settings = get_settings()
    u = cfg.get("redirect_uri") or settings.linear_redirect_uri
    if not u or not str(u).strip():
        raise ValueError("Missing redirect_uri in configuration_data (must match Linear app callback URL).")
    return str(u).strip()


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("access_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def resolve_refresh_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("refresh_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def has_access_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_access_token(cfg))


def resolve_graphql_url(cfg: dict[str, Any]) -> str:
    raw = cfg.get("graphql_url")
    if raw and str(raw).strip():
        return str(raw).strip()
    return LINEAR_GRAPHQL_URL


def team_ids_list(cfg: dict[str, Any]) -> list[str]:
    raw = cfg.get("team_ids") or cfg.get("linear_team_ids")
    if isinstance(raw, str) and raw.strip():
        return [x.strip() for x in raw.split(",") if x.strip()]
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []


def project_ids_list(cfg: dict[str, Any]) -> list[str]:
    raw = cfg.get("project_ids") or cfg.get("linear_project_ids")
    if isinstance(raw, str) and raw.strip():
        return [x.strip() for x in raw.split(",") if x.strip()]
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []
