"""Microsoft Entra token refresh; updates `tool_integrations.configuration_data`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.integrations.categories.idp.microsoft_entra.credentials import (
    OAUTH_CLIENTS_KEY,
    access_token_expires_raw,
    resolve_national_cloud,
    resolve_oauth_application_credentials,
    resolve_refresh_token,
    resolve_scopes,
    resolve_tenant_id,
)
from app.integrations.categories.idp.microsoft_entra.oauth import merge_token_response_into_config, refresh_access_token
from app.models import ToolIntegration


def _cfg(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("configuration_data")
    if isinstance(raw, dict):
        return dict(raw)
    if raw is None:
        return {}
    raise TypeError("configuration_data must be JSON object from DB")


def _parse_expiry(cfg: dict[str, Any]) -> datetime | None:
    raw = access_token_expires_raw(cfg)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def refresh_entra_access_tokens(
    session: Session,
    integration: dict[str, Any],
    *,
    force: bool = False,
) -> tuple[dict[str, Any], bool]:
    cfg = _cfg(integration)
    settings = get_settings()
    cloud = resolve_national_cloud(cfg)
    if not force:
        exp = _parse_expiry(cfg)
        now = datetime.now(timezone.utc)
        if exp and exp > now + timedelta(minutes=2):
            return cfg, False

    refresh = resolve_refresh_token(cfg)
    if not refresh:
        raise ValueError("Missing refresh_token; complete OAuth first.")

    tenant = resolve_tenant_id(cfg)
    try:
        entry = cfg.get(OAUTH_CLIENTS_KEY)
        if isinstance(entry, list) and entry and isinstance(entry[-1], dict):
            tenant = str(entry[-1].get("tenant_id") or tenant)
    except (TypeError, IndexError):
        pass

    client_id, client_secret = resolve_oauth_application_credentials(cfg, settings=settings, cloud=cloud)
    scopes = resolve_scopes(cfg, cloud=cloud)
    token_payload = refresh_access_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh,
        tenant_id=tenant,
        cloud=cloud,
        scopes=scopes,
    )
    new_cfg = merge_token_response_into_config(
        cfg,
        token_payload,
        tenant_id=tenant,
        cloud=cloud,
    )
    ti = session.get(ToolIntegration, integration["id"])
    if not ti:
        raise ValueError("Integration row missing during token refresh.")
    ti.configuration_data = new_cfg
    ti.is_active = True
    session.commit()
    return new_cfg, True


def ensure_fresh_access_token(session: Session, integration: dict[str, Any]) -> dict[str, Any]:
    cfg, _ = refresh_entra_access_tokens(session, integration, force=False)
    return cfg
