"""Refresh Wiz OAuth token when missing (client credentials)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.cspm.wiz import auth
from app.integrations.categories.cspm.wiz.credentials import (
    has_access_token,
    merge_token_into_config,
    resolve_audience,
    resolve_auth_url,
    resolve_client_credentials,
)
from app.integrations.core.persistence import tool_integration_service as persistence


def ensure_fresh_access_token(session: Session, row: dict[str, Any]) -> dict[str, Any]:
    """Return configuration_data; obtain token only if missing."""
    cfg = dict(row["configuration_data"] or {})
    if not isinstance(cfg, dict):
        cfg = {}
    if has_access_token(cfg):
        return cfg
    cid, sec = resolve_client_credentials(cfg)
    token_payload = auth.fetch_client_credentials_token(
        client_id=cid,
        client_secret=sec,
        auth_url=resolve_auth_url(cfg),
        audience=resolve_audience(cfg),
    )
    new_cfg = merge_token_into_config(cfg, token_payload)
    persistence.save_tool_integration_config(session, row["id"], new_cfg)
    return new_cfg


def force_refresh_access_token(session: Session, row: dict[str, Any]) -> dict[str, Any]:
    """Always exchange client credentials and persist new token."""
    cfg = dict(row["configuration_data"] or {})
    if not isinstance(cfg, dict):
        cfg = {}
    cid, sec = resolve_client_credentials(cfg)
    token_payload = auth.fetch_client_credentials_token(
        client_id=cid,
        client_secret=sec,
        auth_url=resolve_auth_url(cfg),
        audience=resolve_audience(cfg),
    )
    new_cfg = merge_token_into_config(cfg, token_payload)
    persistence.save_tool_integration_config(session, row["id"], new_cfg)
    return new_cfg
