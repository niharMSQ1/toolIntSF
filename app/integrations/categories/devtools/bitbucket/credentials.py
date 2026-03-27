"""Resolve OAuth credentials and tokens for Bitbucket Cloud."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.config import Settings, get_settings


def resolve_oauth_credentials(cfg: dict[str, Any], settings: Settings | None = None) -> tuple[str, str, str]:
    """Return (client_id, client_secret, redirect_uri)."""
    s = settings or get_settings()
    cid = cfg.get("client_id") or s.bitbucket_client_id
    sec = cfg.get("client_secret")
    if sec is None or str(sec).strip() == "":
        sec = s.bitbucket_client_secret
    redir = cfg.get("redirect_uri") or s.bitbucket_redirect_uri
    if not cid or not str(cid).strip():
        raise ValueError("Bitbucket client_id is required (configuration_data or BITBUCKET_CLIENT_ID).")
    if sec is None or str(sec).strip() == "":
        raise ValueError("Bitbucket client_secret is required (configuration_data or BITBUCKET_CLIENT_SECRET).")
    if not redir or not str(redir).strip():
        raise ValueError("Bitbucket redirect_uri is required (configuration_data or BITBUCKET_REDIRECT_URI).")
    return str(cid).strip(), str(sec), str(redir).strip()


def has_access_token(cfg: dict[str, Any]) -> bool:
    t = cfg.get("access_token")
    return t is not None and str(t).strip() != ""


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    if not has_access_token(cfg):
        return None
    return str(cfg["access_token"]).strip()


def oauth_complete(cfg: dict[str, Any]) -> bool:
    return bool(cfg.get("oauth_completed_at")) and has_access_token(cfg)


def workspaces_selected(cfg: dict[str, Any]) -> bool:
    raw = cfg.get("selected_workspaces")
    if not isinstance(raw, list) or not raw:
        return False
    return bool(cfg.get("workspace_selection_completed_at"))


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return oauth_complete(cfg) and workspaces_selected(cfg)
