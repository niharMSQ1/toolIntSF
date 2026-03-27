"""ServiceNow ITSM configure endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.itsm.servicenow.collection_runner import (
    run_servicenow_evidence_collection_after_configure_background,
)
from app.integrations.categories.itsm.servicenow.seed_service import seed_servicenow_evidence_masters
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import ServiceNowConfigureResponse, ToolIntegrationPayload

router = APIRouter(prefix="/api/v1/integrations/servicenow", tags=["integrations", "itsm", "servicenow"])
itsm_router = APIRouter(prefix="/itsm/servicenow", tags=["integrations", "itsm", "servicenow"])


def _mask_configuration_data(cfg: dict) -> dict:
    masked = dict(cfg)
    for key in ("password", "api_key", "client_secret"):
        if key in masked and masked[key]:
            masked[key] = "***"
    return masked


def _configure_impl(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session,
) -> ServiceNowConfigureResponse:
    try:
        row = persistence.upsert_tool_integration(
            session,
            org_id=payload.org_id,
            tool_id=payload.tool_id,
            user_id=payload.user_id,
            configuration_data=dict(payload.configuration_data),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    seed_servicenow_evidence_masters(session, payload.tool_id)
    background_tasks.add_task(
        run_servicenow_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return ServiceNowConfigureResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        configured=True,
        collection_started=True,
        next_step=(
            "Integration saved, evidence_masters seeded, and ServiceNow evidence collection started "
            "in the background. Use POST /api/v1/evidence/collect or POST /api/v1/integrations/sync to re-run."
        ),
        configuration_data=_mask_configuration_data(row["configuration_data"]),
    )


@router.post("/configure", response_model=ServiceNowConfigureResponse)
def configure_servicenow(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> ServiceNowConfigureResponse:
    return _configure_impl(payload, background_tasks, session)


@itsm_router.post("/integrations", response_model=ServiceNowConfigureResponse)
def configure_servicenow_alias(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> ServiceNowConfigureResponse:
    return _configure_impl(payload, background_tasks, session)
