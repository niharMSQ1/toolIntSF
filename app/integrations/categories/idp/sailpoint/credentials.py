"""SailPoint Identity Security Cloud (IdentityNow) API base — see developer.sailpoint.com."""

from __future__ import annotations

from typing import Any


def resolve_api_base(cfg: dict[str, Any]) -> str:
    u = cfg.get("sailpoint_base_url") or cfg.get("identitynow_base_url")
    if not u or not str(u).strip():
        raise ValueError(
            "Missing sailpoint_base_url (e.g. https://<tenant>.api.identitynow.com).",
        )
    return str(u).strip().rstrip("/")


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("sailpoint_client_id")
    sec = cfg.get("client_secret") or cfg.get("sailpoint_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id for SailPoint OAuth 2.0.")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret for SailPoint OAuth 2.0.")
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


def resolve_identities_path(cfg: dict[str, Any]) -> str:
    p = cfg.get("sailpoint_identities_path") or cfg.get("identities_path")
    if p and str(p).strip():
        return str(p).strip()
    return "/v3/public-identities"


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    try:
        resolve_api_base(cfg)
    except ValueError:
        return False
    return has_oauth_client(cfg) or has_access_token(cfg)
