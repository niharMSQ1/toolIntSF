"""
Token refresh and on-demand evidence collection for tool integrations.
Exposes endpoints to refresh tokens (if needed) and run collect_and_persist_evidence
for a given integration or all active integrations in an org.
"""
import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from HRMS_Integrations.db import get_db
from HRMS_Integrations.Zoho_people.client import ZohoPeopleClient
from HRMS_Integrations.Zoho_people.service import collect_and_persist_evidence as zoho_collect
from ITSM_Integrations.Jira_servicedesk.client import JiraServicedeskClient
from ITSM_Integrations.Jira_servicedesk.service import collect_and_persist_evidence as jira_collect
from IdP_Integrations.Okta.service import collect_and_persist_evidence as okta_collect
from models import ToolIntegrations, Tools


router = APIRouter(prefix="/integrations", tags=["Evidence collection"])

# Buffer before expiry to trigger refresh (seconds)
REFRESH_BUFFER_SECONDS = 300


def _is_token_expired_soon(expires_at_iso: str | None) -> bool:
    """True if no expiry stored or expiry is within REFRESH_BUFFER_SECONDS from now."""
    if not expires_at_iso:
        return True
    try:
        if expires_at_iso.endswith("Z"):
            expires_at = datetime.datetime.fromisoformat(expires_at_iso.replace("Z", "+00:00"))
        else:
            expires_at = datetime.datetime.fromisoformat(expires_at_iso)
        if expires_at.tzinfo:
            now = datetime.datetime.now(expires_at.tzinfo)
        else:
            now = datetime.datetime.utcnow()
        return (expires_at - now).total_seconds() <= REFRESH_BUFFER_SECONDS
    except (ValueError, TypeError):
        return True


@router.post("/{integration_id}/refresh-and-collect", response_model=dict)
async def refresh_and_collect(
    integration_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict:
    """
    For the given tool integration: refresh access token if expired or expiring soon,
    then run evidence collection (collect_and_persist_evidence). Commits on success.
    """
    integration = db.get(ToolIntegrations, integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    if not integration.is_active:
        raise HTTPException(status_code=400, detail="Integration is not active")

    config = integration.configuration_data or {}
    provider = config.get("provider")

    # Okta: detect by tool name so we use API-token flow even when config was not saved correctly
    tool = db.get(Tools, integration.tool_id) if integration.tool_id else None
    if tool and tool.name and str(tool.name).strip().lower() == "okta":
        provider = "okta"
        if config.get("provider") != "okta":
            config["provider"] = "okta"
            integration.configuration_data = config
    # Else treat as Okta if api_token + org_domain present
    elif config.get("api_token") and config.get("org_domain"):
        provider = "okta"
        if config.get("provider") != "okta":
            config["provider"] = "okta"
            integration.configuration_data = config

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="Integration has no provider set; reconnect via OAuth callback",
        )

    # Okta uses API token only (no OAuth refresh)
    if provider == "okta":
        access_token = config.get("api_token")
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="Okta api_token missing. Reconnect: POST /idp/okta/integrations with body containing configuration_data.api_token and configuration_data.org_domain",
            )
    else:
        access_token = config.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token; reconnect via OAuth callback")

        # Refresh token if needed (Zoho, Jira)
        expires_at = config.get("access_token_expires_at")
        if _is_token_expired_soon(expires_at):
            refresh_token = config.get("refresh_token")
            if not refresh_token:
                raise HTTPException(
                    status_code=400,
                    detail="Token expired and no refresh token; reconnect via OAuth callback",
                )
            if provider == "zoho_people":
                client = ZohoPeopleClient(
                    region=config["region"],
                    client_id=config["client_id"],
                    client_secret=config["client_secret"],
                    redirect_uri=config["redirect_uri"],
                )
                token_payload = await client.refresh_access_token(refresh_token)
            elif provider == "jira_servicedesk":
                client = JiraServicedeskClient(
                    client_id=config["client_id"],
                    client_secret=config["client_secret"],
                    redirect_uri=config["redirect_uri"],
                )
                token_payload = await client.refresh_access_token(refresh_token)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

            new_access = token_payload.get("access_token")
            if not new_access:
                raise HTTPException(status_code=500, detail="Failed to refresh access token")
            config["access_token"] = new_access
            if token_payload.get("refresh_token"):
                config["refresh_token"] = token_payload["refresh_token"]
            expires_in = token_payload.get("expires_in")
            if expires_in is not None:
                config["access_token_expires_at"] = (
                    datetime.datetime.utcnow() + datetime.timedelta(seconds=int(expires_in))
                ).isoformat()
            integration.configuration_data = config
            integration.updated_at = datetime.datetime.utcnow()
            access_token = new_access

    # Run evidence collection
    try:
        if provider == "zoho_people":
            await zoho_collect(db=db, integration=integration, access_token=access_token)
        elif provider == "jira_servicedesk":
            await jira_collect(db=db, integration=integration, access_token=access_token)
        elif provider == "okta":
            await okta_collect(db=db, integration=integration, access_token=access_token)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"status": "ok", "integration_id": str(integration_id), "evidence_collected": True}


@router.post("/refresh-and-collect-by-org", response_model=dict)
async def refresh_and_collect_by_org(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict:
    """
    For all active tool integrations in the given organization, run refresh-and-collect.
    Returns counts of success and failure (first failure detail).
    """
    stmt = (
        select(ToolIntegrations)
        .where(ToolIntegrations.organization_id == organization_id)
        .where(ToolIntegrations.is_active == True)
    )
    integrations = list(db.scalars(stmt).all())
    if not integrations:
        return {
            "status": "ok",
            "organization_id": str(organization_id),
            "total": 0,
            "success": 0,
            "failed": 0,
        }

    success = 0
    failed = 0
    first_error = None
    for integration in integrations:
        try:
            await refresh_and_collect(integration_id=integration.id, db=db)
            success += 1
        except HTTPException as e:
            failed += 1
            if first_error is None:
                first_error = {"integration_id": str(integration.id), "detail": e.detail}
        except Exception as e:
            failed += 1
            if first_error is None:
                first_error = {"integration_id": str(integration.id), "detail": str(e)}

    return {
        "status": "ok",
        "organization_id": str(organization_id),
        "total": len(integrations),
        "success": success,
        "failed": failed,
        "first_error": first_error,
    }
