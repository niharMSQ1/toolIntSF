"""Refresh or obtain Microsoft Graph access token."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.project_management.microsoft_planner.credentials import resolve_refresh_token
from app.integrations.categories.project_management.microsoft_planner.graph_auth import (
    fetch_token_client_credentials,
    fetch_token_refresh,
    merge_token_into_config,
    token_expired,
)
from app.integrations.core.persistence import tool_integration_service as persistence


def ensure_graph_access_token(
    session: Session,
    integration: dict[str, Any],
    *,
    force: bool = False,
) -> tuple[dict[str, Any], str, bool]:
    """
    Returns (configuration_data, access_token, did_fetch_token).
    """
    cfg = dict(integration["configuration_data"] or {})
    if not isinstance(cfg, dict):
        cfg = {}
    tid = str(cfg.get("tenant_id") or "").strip()
    cid = str(cfg.get("client_id") or "").strip()
    csec = str(cfg.get("client_secret") or "").strip()
    existing = str(cfg.get("access_token") or "").strip()

    if existing and not force and not token_expired(cfg):
        return cfg, existing, False

    if not tid or not cid or not csec:
        if existing:
            return cfg, existing, False
        raise ValueError("Missing tenant_id, client_id, client_secret or access_token for Microsoft Graph.")

    rt = resolve_refresh_token(cfg)
    if rt and not force:
        try:
            payload = fetch_token_refresh(tenant_id=tid, client_id=cid, client_secret=csec, refresh_token=rt)
        except Exception:
            payload = fetch_token_client_credentials(tenant_id=tid, client_id=cid, client_secret=csec)
    else:
        payload = fetch_token_client_credentials(tenant_id=tid, client_id=cid, client_secret=csec)

    new_cfg = merge_token_into_config(cfg, payload)
    persistence.save_tool_integration_config(session, integration["id"], new_cfg)
    token = str(new_cfg.get("access_token") or "").strip()
    if not token:
        raise ValueError("Token response missing access_token.")
    return new_cfg, token, True
