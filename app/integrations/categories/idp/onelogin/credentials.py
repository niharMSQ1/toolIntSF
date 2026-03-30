"""OneLogin API — region-specific host; OAuth 2.0 client credentials."""

from __future__ import annotations

from typing import Any


def resolve_region(cfg: dict[str, Any]) -> str:
    r = cfg.get("onelogin_region") or cfg.get("region") or "us"
    return str(r).strip().lower() or "us"


def token_url_for_region(region: str) -> str:
    return f"https://api.{region}.onelogin.com/auth/oauth2/v2/token"


def api_origin_for_region(region: str) -> str:
    return f"https://api.{region}.onelogin.com"


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("onelogin_client_id")
    sec = cfg.get("client_secret") or cfg.get("onelogin_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id for OneLogin OAuth 2.0.")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret for OneLogin OAuth 2.0.")
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


def resolve_users_path(cfg: dict[str, Any]) -> str:
    p = cfg.get("onelogin_users_path") or cfg.get("users_path")
    if p and str(p).strip():
        return str(p).strip()
    return "/api/1/users"


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    return has_oauth_client(cfg) or has_access_token(cfg)
