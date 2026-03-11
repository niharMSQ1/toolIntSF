import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from HRMS_Integrations.db import get_db
from models import ToolIntegrations, Tools
from .client import JiraServicedeskClient
from .config import JIRA_DEFAULT_SCOPE
from .schemas import ToolIntegrationPayload
from .service import collect_and_persist_evidence


router = APIRouter(prefix="/itsm/jira", tags=["ITSM - Jira Service Management"])


@router.post("/integrations", response_model=dict)
async def create_jira_integration(
    payload: ToolIntegrationPayload,
    db: Session = Depends(get_db),
):
    """
    Create/update Jira Service Management tool integration row and
    return authorization URL to redirect the user.
    """
    tool = db.get(Tools, payload.tool_id)
    if not tool or tool.status != "active":
        raise HTTPException(status_code=400, detail="Invalid or inactive tool_id")

    stmt = (
        select(ToolIntegrations)
        .where(ToolIntegrations.organization_id == payload.org_id)
        .where(ToolIntegrations.user_id == payload.user_id)
        .where(ToolIntegrations.tool_id == payload.tool_id)
    )
    integration = db.scalars(stmt).first()

    if integration is None:
        integration = ToolIntegrations(
            id=uuid.uuid4(),
            organization_id=payload.org_id,
            user_id=payload.user_id,
            tool_id=payload.tool_id,
            is_active=False,
            configuration_data={},
            created_at=datetime.datetime.utcnow(),
        )
        db.add(integration)

    config_dict = integration.configuration_data or {}
    config_dict.update(
        {
            "client_id": payload.configuration_data.client_id,
            "client_secret": payload.configuration_data.client_secret,
            "redirect_uri": payload.configuration_data.redirect_uri,
        }
    )
    integration.configuration_data = config_dict
    integration.updated_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(integration)

    jira_client = JiraServicedeskClient(
        client_id=payload.configuration_data.client_id,
        client_secret=payload.configuration_data.client_secret,
        redirect_uri=payload.configuration_data.redirect_uri,
    )

    state = str(integration.id)
    auth_url = jira_client.build_authorization_url(scope=JIRA_DEFAULT_SCOPE, state=state)

    return {"authorization_url": auth_url, "integration_id": str(integration.id)}


@router.get("/callback")
async def jira_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Atlassian OAuth callback.
    - state = tool_integration.id
    - Exchange code for tokens, get accessible-resources (cloud_id), store all in config.
    - Run evidence collection and mapping in one transaction, then redirect.
    """
    try:
        integration_id = uuid.UUID(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state")

    integration = db.get(ToolIntegrations, integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Tool integration not found")

    config = integration.configuration_data or {}
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    redirect_uri = config.get("redirect_uri")

    if not all([client_id, client_secret, redirect_uri]):
        raise HTTPException(status_code=500, detail="Incomplete Jira configuration in integration")

    jira_client = JiraServicedeskClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    try:
        token_payload = await jira_client.exchange_code_for_tokens(code)
        access_token = token_payload.get("access_token")
        refresh_token = token_payload.get("refresh_token")
        expires_in = token_payload.get("expires_in")

        if not access_token:
            raise HTTPException(status_code=500, detail="Failed to obtain access token from Atlassian")

        config["access_token"] = access_token
        if refresh_token:
            config["refresh_token"] = refresh_token
        if expires_in is not None:
            config["access_token_expires_at"] = (
                datetime.datetime.utcnow() + datetime.timedelta(seconds=int(expires_in))
            ).isoformat()

        resources = await jira_client.get_accessible_resources(access_token)
        if not resources or not isinstance(resources, list):
            raise HTTPException(status_code=500, detail="No accessible Jira sites returned")
        first = resources[0]
        cloud_id = first.get("id") if isinstance(first, dict) else None
        if not cloud_id:
            raise HTTPException(status_code=500, detail="Could not determine cloud_id from accessible resources")
        config["cloud_id"] = str(cloud_id)

        integration.configuration_data = config
        integration.is_active = True
        integration.updated_at = datetime.datetime.utcnow()

        await collect_and_persist_evidence(
            db=db,
            integration=integration,
            access_token=access_token,
        )

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return RedirectResponse(url="http://192.168.6.4/evidence/all-evidence")
