"""Refresh Asana OAuth access tokens when expired (PAT path unchanged)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.project_management.asana.credentials import (
    resolve_oauth_credentials,
    resolve_refresh_token,
    uses_personal_access_token,
)
from app.integrations.categories.project_management.asana.oauth import merge_token_response_into_config, refresh_access_token
from app.integrations.core.persistence import tool_integration_service as persistence


def _token_expired(cfg: dict[str, Any], *, skew_seconds: int = 120) -> bool:
    raw = cfg.get("access_token_expires_at")
    if not raw or not str(raw).strip():
        return True
    try:
        exp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return True
    now = datetime.now(timezone.utc)
    return now >= exp - timedelta(seconds=skew_seconds)


def refresh_asana_access_tokens(
    session: Session,
    integration: dict[str, Any],
    *,
    force: bool = False,
) -> tuple[dict[str, Any], bool]:
    """
    Returns (updated configuration_data, did_call_token_endpoint).
    Raises ValueError if OAuth is required but refresh is not possible.
    """
    cfg = dict(integration["configuration_data"] or {})
    if not isinstance(cfg, dict):
        cfg = {}
    if uses_personal_access_token(cfg):
        return cfg, False
    if not cfg.get("access_token"):
        raise ValueError("No access_token; complete OAuth or set personal_access_token.")
    rt = resolve_refresh_token(cfg)
    if not rt:
        raise ValueError("No refresh_token; re-authorize Asana OAuth.")
    if not force and not _token_expired(cfg):
        return cfg, False
    client_id, client_secret = resolve_oauth_credentials(cfg)
    token_payload = refresh_access_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=rt,
    )
    new_cfg = merge_token_response_into_config(cfg, token_payload)
    persistence.save_tool_integration_config(session, integration["id"], new_cfg)
    return new_cfg, True
