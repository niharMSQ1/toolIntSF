"""Refresh Bitbucket access tokens when expired or near expiry."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.devtools.bitbucket.credentials import resolve_oauth_credentials
from app.integrations.categories.devtools.bitbucket.oauth import merge_token_response_into_config, refresh_access_token
from app.integrations.core.persistence import tool_integration_service as persistence


def _parse_iso(dt: str | None) -> datetime | None:
    if not dt or not str(dt).strip():
        return None
    try:
        raw = str(dt).strip().replace("Z", "+00:00")
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def ensure_fresh_access_token(session: Session, integration: dict[str, Any]) -> dict[str, Any]:
    """Return configuration_data with a valid access_token (refresh if needed)."""
    cfg = integration.get("configuration_data")
    if not isinstance(cfg, dict):
        return {}
    if not cfg.get("access_token"):
        return cfg
    exp = _parse_iso(cfg.get("access_token_expires_at"))
    refresh_tok = cfg.get("refresh_token")
    if exp is None or refresh_tok is None:
        return cfg
    now = datetime.now(timezone.utc)
    if exp > now and (exp - now).total_seconds() > 120:
        return cfg
    client_id, client_secret, _ = resolve_oauth_credentials(cfg)
    try:
        token_payload = refresh_access_token(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=str(refresh_tok),
        )
    except Exception:
        return cfg
    new_cfg = merge_token_response_into_config(cfg, token_payload, clear_workspace_selection=False)
    persistence.save_tool_integration_config(session, integration["id"], new_cfg)
    return new_cfg
