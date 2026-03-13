"""
Okta integration routes. API-token based (no OAuth callback).
POST /idp/okta/integrations: save integration then call refresh-and-collect internally (single code path, one user step).
"""
import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from HRMS_Integrations.db import get_db
from integration_collection import refresh_and_collect
from models import ToolIntegrations, Tools
from .schemas import ToolIntegrationPayload


router = APIRouter(prefix="/idp/okta", tags=["IdP - Okta"])


@router.post("/integrations", response_model=dict)
async def create_okta_integration(
    payload: ToolIntegrationPayload,
    db: Session = Depends(get_db),
):
    """
    Create or update Okta tool integration, then run refresh-and-collect internally.
    Single step for user; no second request. Uses the same code path as POST /integrations/{id}/refresh-and-collect.
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
            "org_domain": payload.configuration_data.org_domain,
            "api_token": payload.configuration_data.api_token,
            "provider": "okta",
        }
    )
    integration.configuration_data = config_dict
    integration.is_active = True
    integration.updated_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(integration)

    # Hit refresh-and-collect internally (single code path; no duplicated logic)
    return await refresh_and_collect(integration_id=integration.id, db=db)


@router.post("/integrations/{integration_id}/collect", response_model=dict)
async def collect_okta_evidence(
    integration_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Run Okta evidence collection for the given integration (API token from config).
    """
    integration = db.get(ToolIntegrations, integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    if not integration.is_active:
        raise HTTPException(status_code=400, detail="Integration is not active")

    config = integration.configuration_data or {}
    api_token = config.get("api_token")
    org_domain = config.get("org_domain")
    if not api_token or not org_domain:
        raise HTTPException(
            status_code=400,
            detail="Okta integration requires api_token and org_domain in configuration",
        )

    try:
        await collect_and_persist_evidence(
            db=db,
            integration=integration,
            access_token=api_token,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"status": "ok", "integration_id": str(integration_id), "evidence_collected": True}
