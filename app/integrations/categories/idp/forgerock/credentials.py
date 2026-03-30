"""ForgeRock / PingAM-style OAuth2 — token URL and resource base are deployment-specific."""

from __future__ import annotations

from typing import Any


def resolve_token_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("forgerock_token_url") or cfg.get("oauth_token_url")
    if not u or not str(u).strip():
        raise ValueError(
            "Missing forgerock_token_url (full POST URL for OAuth2 token, e.g. AM access_token endpoint).",
        )
    return str(u).strip().rstrip("/")


def resolve_api_base(cfg: dict[str, Any]) -> str:
    u = cfg.get("forgerock_api_base") or cfg.get("api_base_url")
    if not u or not str(u).strip():
        raise ValueError("Missing forgerock_api_base (REST API origin for user resources).")
    return str(u).strip().rstrip("/")


def resolve_users_path(cfg: dict[str, Any]) -> str:
    p = cfg.get("forgerock_users_path") or cfg.get("users_path")
    if p and str(p).strip():
        return str(p).strip()
    return "/openidm/managed/user?_queryFilter=true"


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("forgerock_client_id")
    sec = cfg.get("client_secret") or cfg.get("forgerock_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id for ForgeRock OAuth 2.0.")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret for ForgeRock OAuth 2.0.")
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


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    try:
        resolve_token_url(cfg)
        resolve_api_base(cfg)
    except ValueError:
        return False
    return has_oauth_client(cfg) or has_access_token(cfg)
