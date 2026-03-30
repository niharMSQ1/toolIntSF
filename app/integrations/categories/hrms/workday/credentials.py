"""Workday configuration_data: hostname, tenant, OAuth client, tokens."""

from __future__ import annotations

from typing import Any


def resolve_hostname(cfg: dict[str, Any]) -> str:
    h = cfg.get("workday_hostname") or cfg.get("hostname") or cfg.get("base_url")
    if not h or not str(h).strip():
        raise ValueError(
            "Missing workday_hostname in configuration_data (e.g. https://impl-services1.workday.com).",
        )
    return str(h).strip().rstrip("/")


def resolve_tenant(cfg: dict[str, Any]) -> str:
    t = cfg.get("workday_tenant") or cfg.get("tenant")
    if not t or not str(t).strip():
        raise ValueError("Missing workday_tenant in configuration_data (tenant name used in REST and OAuth paths).")
    return str(t).strip()


def resolve_api_version(cfg: dict[str, Any]) -> str:
    v = cfg.get("api_version") or cfg.get("workday_api_version")
    if v and str(v).strip():
        v = str(v).strip()
        return v if v.startswith("v") else f"v{v}"
    from app.integrations.categories.hrms.workday.constants import DEFAULT_API_VERSION

    return DEFAULT_API_VERSION


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("workday_client_id")
    sec = cfg.get("client_secret") or cfg.get("workday_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id (or workday_client_id) for OAuth 2.0.")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret (or workday_client_secret) for OAuth 2.0.")
    return str(cid).strip(), str(sec).strip()


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("access_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def has_oauth_client(cfg: dict[str, Any]) -> bool:
    try:
        resolve_oauth_client(cfg)
        return True
    except ValueError:
        return False


def has_access_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_access_token(cfg))


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    try:
        resolve_hostname(cfg)
        resolve_tenant(cfg)
    except ValueError:
        return False
    return has_access_token(cfg)
