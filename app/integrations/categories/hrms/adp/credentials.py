"""ADP API: OAuth 2.0 + API host (ADP Marketplace / developer documentation)."""

from __future__ import annotations

from typing import Any

DEFAULT_ADP_TOKEN_URL = "https://accounts.adp.com/auth/oauth/v2/token"
DEFAULT_ADP_API_BASE = "https://api.adp.com"


def resolve_token_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("adp_token_url") or cfg.get("oauth_token_url")
    if u and str(u).strip():
        return str(u).strip().rstrip("/")
    return DEFAULT_ADP_TOKEN_URL


def resolve_api_base(cfg: dict[str, Any]) -> str:
    u = cfg.get("adp_api_base") or cfg.get("api_base_url")
    if u and str(u).strip():
        return str(u).strip().rstrip("/")
    return DEFAULT_ADP_API_BASE


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("adp_client_id")
    sec = cfg.get("client_secret") or cfg.get("adp_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id for ADP OAuth 2.0.")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret for ADP OAuth 2.0.")
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
    return bool(resolve_access_token(cfg))
