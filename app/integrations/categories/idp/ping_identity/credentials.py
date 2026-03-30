"""Resolve PingOne Platform API settings from tool_integrations.configuration_data."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.ping_identity.constants import DEFAULT_REGION_TLD


def resolve_region_tld(cfg: dict[str, Any]) -> str:
    t = cfg.get("pingone_region_tld") or cfg.get("region_tld") or cfg.get("tld")
    if t and str(t).strip():
        return str(t).strip().lower()
    return DEFAULT_REGION_TLD


def resolve_auth_base(cfg: dict[str, Any]) -> str:
    u = cfg.get("pingone_auth_base") or cfg.get("auth_base_url")
    if u and str(u).strip():
        return str(u).strip().rstrip("/")
    tld = resolve_region_tld(cfg)
    return f"https://auth.pingone.{tld}"


def resolve_api_base(cfg: dict[str, Any]) -> str:
    u = cfg.get("pingone_api_base") or cfg.get("api_base_url")
    if u and str(u).strip():
        return str(u).strip().rstrip("/")
    tld = resolve_region_tld(cfg)
    return f"https://api.pingone.{tld}/v1"


def resolve_environment_id(cfg: dict[str, Any]) -> str:
    e = cfg.get("pingone_environment_id") or cfg.get("environment_id")
    if not e or not str(e).strip():
        raise ValueError(
            "Missing pingone_environment_id (PingOne environment UUID from the admin console).",
        )
    return str(e).strip()


def resolve_token_environment_id(cfg: dict[str, Any]) -> str:
    """Environment ID used in POST .../as/token (Worker app environment). Defaults to pingone_environment_id."""
    t = cfg.get("pingone_token_environment_id") or cfg.get("token_environment_id")
    if t and str(t).strip():
        return str(t).strip()
    return resolve_environment_id(cfg)


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("pingone_client_id")
    sec = cfg.get("client_secret") or cfg.get("pingone_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id for PingOne Worker application (OAuth 2.0).")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret for PingOne Worker application.")
    return str(cid).strip(), str(sec).strip()


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("access_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def has_access_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_access_token(cfg))


def has_oauth_client(cfg: dict[str, Any]) -> bool:
    try:
        resolve_oauth_client(cfg)
        return True
    except ValueError:
        return False


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    try:
        resolve_api_base(cfg)
        resolve_environment_id(cfg)
    except ValueError:
        return False
    return bool(resolve_access_token(cfg))


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    """True when OAuth client is present (token obtained on configure) or access_token already stored."""
    if not isinstance(cfg, dict):
        return False
    try:
        resolve_environment_id(cfg)
        resolve_api_base(cfg)
        resolve_auth_base(cfg)
    except ValueError:
        return False
    return has_oauth_client(cfg) or bool(resolve_access_token(cfg))
