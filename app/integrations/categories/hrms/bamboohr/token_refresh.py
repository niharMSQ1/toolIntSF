"""Refresh BambooHR app/OAuth access tokens.

Why this file matters in the workflow:
- OAuth callback stores the first access token
- later API calls need a token that is still valid
- this module is the bridge between "OAuth once" and "keep working over time"

API key mode does not need token refresh, so this file mainly serves app/OAuth mode.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.hrms.bamboohr.credentials import (
    AUTH_MODE_API_KEY,
    access_token_expires_raw,
    resolve_auth_mode,
    resolve_client_credentials,
    resolve_redirect_uri,
    resolve_refresh_token,
    resolve_subdomain,
)
from app.integrations.categories.hrms.bamboohr.oauth import merge_token_response_into_config, refresh_access_token
from app.integrations.core.persistence import tool_integration_service as persistence


def _cfg(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize configuration_data into a mutable dict."""
    raw = row.get("configuration_data")
    if isinstance(raw, dict):
        return dict(raw)
    if raw is None:
        return {}
    raise TypeError("configuration_data must be JSON object from DB")


def _parse_expiry(cfg: dict[str, Any]) -> datetime | None:
    """Parse ISO token expiry, returning None when missing or invalid."""
    raw = access_token_expires_raw(cfg)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def refresh_bamboohr_access_tokens(
    session: Session,
    integration: dict[str, Any],
    *,
    force: bool = False,
) -> tuple[dict[str, Any], bool]:
    """Refresh BambooHR app-auth access tokens when needed.

    Returns:
    - updated configuration_data
    - bool telling the caller whether a refresh call happened
    """
    cfg = _cfg(integration)
    mode = resolve_auth_mode(cfg)

    if mode == AUTH_MODE_API_KEY:
        return cfg, False

    if not force:
        exp = _parse_expiry(cfg)
        now = datetime.now(timezone.utc)
        if exp and exp > now + timedelta(minutes=2):
            return cfg, False

    refresh_token = resolve_refresh_token(cfg)
    if not refresh_token:
        raise ValueError("Missing BambooHR refresh_token; complete app OAuth first.")

    company_domain = resolve_subdomain(cfg)
    client_id, client_secret = resolve_client_credentials(cfg)
    redirect_uri = resolve_redirect_uri(cfg)

    token_payload = refresh_access_token(
        company_domain=company_domain,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        redirect_uri=redirect_uri,
    )
    new_cfg = merge_token_response_into_config(cfg, token_payload)
    persistence.save_tool_integration_config(session, integration["id"], new_cfg)
    return new_cfg, True


def ensure_fresh_credentials(session: Session, integration: dict[str, Any]) -> dict[str, Any]:
    """Return a BambooHR config that is safe for immediate API use.

    API key mode:
    - returns config unchanged

    App/OAuth mode:
    - refreshes if the access token is close to expiry
    """
    cfg, _ = refresh_bamboohr_access_tokens(session, integration, force=False)
    return cfg
