"""Google Workspace Admin SDK — Directory API (OAuth 2.0)."""

from __future__ import annotations

from typing import Any

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_DIRECTORY_BASE = "https://admin.googleapis.com"


def resolve_workspace_domain(cfg: dict[str, Any]) -> str:
    d = cfg.get("google_workspace_domain") or cfg.get("primary_domain")
    if not d or not str(d).strip():
        raise ValueError("Missing google_workspace_domain (primary Google Workspace domain).")
    return str(d).strip().lower()


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("google_client_id")
    sec = cfg.get("client_secret") or cfg.get("google_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id (Google OAuth client).")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret (Google OAuth client).")
    return str(cid).strip(), str(sec).strip()


def resolve_refresh_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("refresh_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("access_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def has_refresh_flow(cfg: dict[str, Any]) -> bool:
    try:
        resolve_oauth_client(cfg)
    except ValueError:
        return False
    return bool(resolve_refresh_token(cfg))


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    try:
        resolve_workspace_domain(cfg)
    except ValueError:
        return False
    return bool(resolve_access_token(cfg)) or has_refresh_flow(cfg)
