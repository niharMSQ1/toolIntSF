"""Refresh Jira Cloud OAuth access tokens."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.itsm.jira import oauth
from app.integrations.categories.itsm.jira.credentials import (
    resolve_oauth_credentials,
    resolve_refresh_token,
)
from app.integrations.core.persistence import tool_integration_service as persistence


def refresh_jira_access_tokens(session: Session, row: dict[str, Any], *, force: bool = False) -> tuple[dict[str, Any], bool]:
    """
    Refresh access token when force=True, or when access token is missing but refresh exists.
    Returns (new_configuration_data, did_refresh).
    """
    cfg = dict(row["configuration_data"] or {})
    if not isinstance(cfg, dict):
        cfg = {}

    if not force and cfg.get("access_token"):
        return cfg, False

    rt = resolve_refresh_token(cfg)
    if not rt:
        raise ValueError("No refresh_token stored; complete OAuth again.")

    cid, sec = resolve_oauth_credentials(cfg)
    token_payload = oauth.refresh_access_token(client_id=cid, client_secret=sec, refresh_token=rt)
    new_cfg = oauth.merge_token_response_into_config(cfg, token_payload)
    persistence.save_tool_integration_config(session, row["id"], new_cfg)
    return new_cfg, True
