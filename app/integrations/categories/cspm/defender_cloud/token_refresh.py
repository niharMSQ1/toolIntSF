"""Persist Azure AD access token for ARM (Defender for Cloud) calls."""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.cspm.defender_cloud import api_client
from app.integrations.categories.cspm.defender_cloud.credentials import (
    resolve_client_id,
    resolve_client_secret,
    resolve_tenant_id,
)
from app.integrations.core.persistence import tool_integration_service as persistence


def _expires_at(cfg: dict[str, Any]) -> float | None:
    v = cfg.get("azure_token_expires_at")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def ensure_arm_access_token(session: Session, integration_row: dict[str, Any]) -> dict[str, Any]:
    """Return configuration_data with a valid azure_access_token for management.azure.com."""
    cfg = dict(integration_row.get("configuration_data") or {})
    tenant = resolve_tenant_id(cfg)
    cid = resolve_client_id(cfg)
    csec = resolve_client_secret(cfg)
    if not tenant or not cid or not csec:
        return cfg

    token = cfg.get("azure_access_token")
    exp = _expires_at(cfg)
    if token and str(token).strip() and exp is not None and time.time() < exp:
        return cfg

    access, expires_at = api_client.get_client_credentials_token(tenant, cid, csec)
    new_cfg = dict(cfg)
    new_cfg["azure_access_token"] = access
    new_cfg["azure_token_expires_at"] = expires_at
    persistence.save_tool_integration_config(session, integration_row["id"], new_cfg)
    return new_cfg
