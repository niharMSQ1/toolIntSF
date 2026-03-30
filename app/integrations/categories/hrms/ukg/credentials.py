"""UKG: tenant-specific OAuth token URL and API base (per UKG product documentation)."""

from __future__ import annotations

from typing import Any


def resolve_token_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("ukg_token_url") or cfg.get("oauth_token_url")
    if not u or not str(u).strip():
        raise ValueError("Missing ukg_token_url (OAuth 2.0 token endpoint from UKG admin / docs).")
    return str(u).strip().rstrip("/")


def resolve_api_base(cfg: dict[str, Any]) -> str:
    u = cfg.get("ukg_api_base") or cfg.get("api_base_url")
    if not u or not str(u).strip():
        raise ValueError("Missing ukg_api_base (REST API base URL for your UKG product).")
    return str(u).strip().rstrip("/")


def resolve_people_path(cfg: dict[str, Any]) -> str:
    p = cfg.get("ukg_people_path") or cfg.get("people_path")
    if p and str(p).strip():
        return str(p).strip()
    return "/personnel/v1/people"


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("ukg_client_id")
    sec = cfg.get("client_secret") or cfg.get("ukg_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id for UKG OAuth 2.0.")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret for UKG OAuth 2.0.")
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
    try:
        resolve_api_base(cfg)
    except ValueError:
        return False
    return bool(resolve_access_token(cfg))
