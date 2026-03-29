"""Refresh Snyk OAuth client-credentials access token before it expires."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.cspm.snyk.credentials import (
    AUTH_TYPE_OAUTH2,
    oauth_client_credentials_present,
    resolve_auth_type,
    resolve_oauth_client_id,
    resolve_oauth_client_secret,
)
from app.integrations.categories.cspm.snyk.oauth import exchange_client_credentials, merge_oauth_token_into_config
from app.integrations.core.persistence import tool_integration_service as persistence


def _parse_iso(dt: str | None) -> datetime | None:
    if not dt or not str(dt).strip():
        return None
    try:
        raw = str(dt).strip().replace("Z", "+00:00")
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def ensure_fresh_snyk_credentials(session: Session, integration: dict[str, Any]) -> dict[str, Any]:
    """
    For OAuth2 service accounts, re-exchange client_credentials when the access token is missing
    or near expiry. Static api_key / access_token configs are returned unchanged.
    """
    cfg = integration.get("configuration_data")
    if not isinstance(cfg, dict):
        return {}
    if resolve_auth_type(cfg) != AUTH_TYPE_OAUTH2:
        return cfg
    if not oauth_client_credentials_present(cfg):
        return cfg

    exp = _parse_iso(cfg.get("oauth_token_expires_at"))
    now = datetime.now(timezone.utc)
    tok = cfg.get("oauth_access_token")
    if tok and str(tok).strip() and exp and exp > now and (exp - now).total_seconds() > 120:
        return cfg

    region = cfg.get("region")
    region_s = str(region).strip() if region is not None and str(region).strip() else None
    try:
        payload = exchange_client_credentials(
            resolve_oauth_client_id(cfg) or "",
            resolve_oauth_client_secret(cfg) or "",
            region_s,
        )
    except Exception:
        return cfg
    new_cfg = merge_oauth_token_into_config(cfg, payload)
    persistence.save_tool_integration_config(session, integration["id"], new_cfg)
    return new_cfg
