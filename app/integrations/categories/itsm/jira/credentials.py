"""Resolve Jira / Atlassian OAuth credentials from tool_integrations.configuration_data."""

from __future__ import annotations

from typing import Any


def resolve_oauth_credentials(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id")
    sec = cfg.get("client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id in configuration_data (Atlassian OAuth app).")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret in configuration_data.")
    return str(cid).strip(), str(sec).strip()


def resolve_redirect_uri(cfg: dict[str, Any]) -> str:
    u = cfg.get("redirect_uri")
    if not u or not str(u).strip():
        raise ValueError("Missing redirect_uri in configuration_data (must match Atlassian app callback URL).")
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


def resolve_cloud_id(cfg: dict[str, Any]) -> str | None:
    c = cfg.get("atlassian_cloud_id")
    if c and str(c).strip():
        return str(c).strip()
    return None


def project_keys_list(cfg: dict[str, Any]) -> list[str]:
    raw = cfg.get("project_keys") or cfg.get("jira_project_keys")
    if isinstance(raw, str) and raw.strip():
        return [x.strip() for x in raw.split(",") if x.strip()]
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []
