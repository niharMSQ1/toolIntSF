import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from HRMS_Integrations.db import get_db
from models import ToolIntegrations, Tools
from .client import ZohoPeopleClient
from .config import ZOHO_DEFAULT_SCOPE
from .schemas import ToolIntegrationPayload
from .service import collect_and_persist_evidence


router = APIRouter(prefix="/hrms/zoho", tags=["HRMS - Zoho People"])


@router.post("/integrations", response_model=dict)
async def create_zoho_integration(
    payload: ToolIntegrationPayload,
    db: Session = Depends(get_db),
):
    """
    Create/update Zoho People tool integration row and
    return authorization URL to redirect the user.
    """
    # Ensure tool exists and is active for the given tool_id
    tool = db.get(Tools, payload.tool_id)
    if not tool or tool.status != "active":
        raise HTTPException(status_code=400, detail="Invalid or inactive tool_id")

    # Either find existing integration for org+user+tool or create a new one
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

    # Merge/overwrite configuration_data with incoming Zoho config
    config_dict = integration.configuration_data or {}
    config_dict.update(
        {
            "client_id": payload.configuration_data.client_id,
            "client_secret": payload.configuration_data.client_secret,
            "redirect_uri": payload.configuration_data.redirect_uri,
            "region": payload.configuration_data.region,
        }
    )
    integration.configuration_data = config_dict
    integration.updated_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(integration)

    # Build Zoho authorization URL
    zoho_client = ZohoPeopleClient(
        region=payload.configuration_data.region,
        client_id=payload.configuration_data.client_id,
        client_secret=payload.configuration_data.client_secret,
        redirect_uri=payload.configuration_data.redirect_uri,
    )

    # Always use backend‑defined default scope for all organizations
    state = str(integration.id)
    auth_url = zoho_client.build_authorization_url(scope=ZOHO_DEFAULT_SCOPE, state=state)

    return {"authorization_url": auth_url, "integration_id": str(integration.id)}


@router.get("/callback")
async def zoho_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Zoho OAuth callback.

    - state carries tool_integration.id
    - code is the Zoho auth code
    - we store auth_code + tokens in configuration_data
    - then trigger evidence collection and mappings
    - finally redirect to evidence listing page
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
    region = config.get("region")

    if not all([client_id, client_secret, redirect_uri, region]):
        raise HTTPException(status_code=500, detail="Incomplete Zoho configuration in integration")

    zoho_client = ZohoPeopleClient(
        region=region,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    # Run entire flow in one transaction: commit only when everything succeeds.
    # On any failure, roll back so DB is unchanged (no partial creates/updates).
    try:
        # Store auth_code (in transaction, not committed yet)
        config["auth_code"] = code
        integration.configuration_data = config

        # Exchange code for tokens (external call; no DB write)
        token_payload = await zoho_client.exchange_code_for_tokens(code)
        access_token = token_payload.get("access_token")
        refresh_token = token_payload.get("refresh_token")
        expires_in = token_payload.get("expires_in")

        if not access_token:
            raise HTTPException(status_code=500, detail="Failed to obtain access token from Zoho")

        config["access_token"] = access_token
        if refresh_token:
            config["refresh_token"] = refresh_token
        if expires_in:
            config["access_token_expires_at"] = (
                datetime.datetime.utcnow() + datetime.timedelta(seconds=int(expires_in))
            ).isoformat()

        integration.configuration_data = config
        integration.is_active = True
        integration.updated_at = datetime.datetime.utcnow()

        # Evidence creation & mapping (all in same transaction)
        await collect_and_persist_evidence(
            db=db,
            integration=integration,
            access_token=access_token,
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    # Final redirect to evidence listing page
    return RedirectResponse(url="http://192.168.6.4/evidence/all-evidence")

