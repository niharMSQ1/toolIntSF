"""
Helpers for working with tool_integrations for Zoho People.
No schema changes; we only read/write existing tables.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models import Tool, ToolIntegration
from app.services.hrms.zoho.client import (
    ACCOUNTS_BASE,
    build_authorize_url,
    exchange_auth_code_for_tokens,
)

# Fixed IDs provided by you
FIXED_USER_ID = UUID("019c89fe-d390-729d-aea5-6c540886cf3c")
FIXED_ORG_ID = UUID("019c89fe-d268-7298-ac14-6c221fd8d830")


def _now() -> datetime:
    return datetime.utcnow()


def get_zoho_tool(db: Session) -> Tool:
    tool = db.query(Tool).filter(Tool.name == "Zoho People").first()
    if not tool:
        raise ValueError("Tool 'Zoho People' not found in tools table")
    return tool


def init_zoho_integration(
    db: Session,
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    region: str = "com",
    scope: str | None = None,
) -> Tuple[ToolIntegration, str]:
    """
    Create a tool_integrations row for Zoho People with client_id/client_secret,
    and return (integration, authorize_url) for the user to visit.
    """
    tool = get_zoho_tool(db)
    region = region if region in ACCOUNTS_BASE else "com"
    scope = scope or "ZOHOPEOPLE.forms.READ"

    config: dict[str, Any] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "region": region,
        "scope": scope,
    }

    integration = ToolIntegration(
        id=uuid4(),
        user_id=FIXED_USER_ID,
        organization_id=FIXED_ORG_ID,
        tool_id=tool.id,
        configuration_data=config,
        is_active=True,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)

    authorize_url = build_authorize_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        region=region,
        scope=scope,
        state=str(integration.id),
    )
    return integration, authorize_url


def store_zoho_auth_code_and_tokens(
    db: Session,
    *,
    integration_id: UUID,
    auth_code: str,
    region_override: str | None = None,
) -> ToolIntegration:
    """
    Given an auth_code from Zoho redirect, exchange it for access+refresh tokens
    and store them in tool_integrations.configuration_data.
    Use region_override when Zoho redirects with location=in/eu/au (e.g. from callback query).
    """
    integ = db.query(ToolIntegration).filter(ToolIntegration.id == integration_id).first()
    if not integ:
        raise ValueError("tool_integration not found")

    config = dict(integ.configuration_data or {})
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    redirect_uri = config.get("redirect_uri")
    region = region_override or config.get("region", "com")
    if not (client_id and client_secret and redirect_uri):
        raise ValueError("Missing client_id, client_secret or redirect_uri in configuration_data")

    token_data = exchange_auth_code_for_tokens(
        client_id=client_id,
        client_secret=client_secret,
        code=auth_code,
        redirect_uri=redirect_uri,
        region=region,
    )

    config["auth_code"] = auth_code
    config["region"] = region  # use the region we actually used (e.g. in for Zoho India)
    if "access_token" in token_data:
        config["access_token"] = token_data["access_token"]
    if "refresh_token" in token_data:
        config["refresh_token"] = token_data["refresh_token"]
    if "api_domain" in token_data:
        config["api_domain"] = token_data["api_domain"]
    config["token_received_at"] = _now().isoformat()

    integ.configuration_data = config
    integ.updated_at = _now()
    db.commit()
    db.refresh(integ)
    return integ


def get_zoho_sync_config(
    db: Session,
    *,
    integration_id: UUID,
) -> Tuple[str, str, str, str, UUID, UUID]:
    """
    Read tool_integrations row and return (client_id, client_secret, refresh_token, region, organization_id, tool_id).
    """
    integ = db.query(ToolIntegration).filter(ToolIntegration.id == integration_id).first()
    if not integ:
        raise ValueError("tool_integration not found")
    config = integ.configuration_data or {}
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    refresh_token = config.get("refresh_token")
    region = config.get("region", "com")
    if not (client_id and client_secret and refresh_token):
        raise ValueError("Missing client_id, client_secret or refresh_token in configuration_data")
    return client_id, client_secret, refresh_token, region, integ.organization_id, integ.tool_id


def get_zoho_sync_config_by_org(
    db: Session,
    *,
    organization_id: UUID,
) -> Tuple[str, str, str, str, UUID, UUID]:
    """
    Find tool_integrations row by organization_id and Zoho People tool_id;
    return (client_id, client_secret, refresh_token, region, organization_id, tool_id).
    Uses configuration_data for credentials.
    """
    tool = get_zoho_tool(db)
    integ = (
        db.query(ToolIntegration)
        .filter(
            ToolIntegration.organization_id == organization_id,
            ToolIntegration.tool_id == tool.id,
            ToolIntegration.is_active == True,
        )
        .first()
    )
    if not integ:
        raise ValueError(
            f"No active Zoho People integration found for organization_id={organization_id}"
        )
    config = integ.configuration_data or {}
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    refresh_token = config.get("refresh_token")
    region = config.get("region", "com")
    if not (client_id and client_secret and refresh_token):
        raise ValueError("Missing client_id, client_secret or refresh_token in configuration_data")
    return client_id, client_secret, refresh_token, region, integ.organization_id, integ.tool_id

