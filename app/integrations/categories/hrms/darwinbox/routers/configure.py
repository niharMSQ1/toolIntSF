"""Darwinbox-style mock HRMS configure endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.darwinbox.collection_runner import (
    run_darwinbox_evidence_collection_after_configure_background,
)
from app.integrations.categories.hrms.darwinbox.seed_service import seed_darwinbox_evidence_masters
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import DarwinboxConfigureResponse, ToolIntegrationPayload

router = APIRouter(prefix="/api/v1/integrations/darwinbox", tags=["integrations", "hrms", "darwinbox"])
hrms_router = APIRouter(prefix="/hrms/darwinbox", tags=["integrations", "hrms", "darwinbox"])


def _configure_impl(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session,
) -> DarwinboxConfigureResponse:
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

    seed_darwinbox_evidence_masters(session, payload.tool_id)
    background_tasks.add_task(
        run_darwinbox_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return DarwinboxConfigureResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        configured=True,
        collection_started=True,
        next_step=(
            "Integration saved, evidence_masters seeded, and Darwinbox evidence collection started "
            "in the background. Use POST /api/v1/evidence/collect or POST /api/v1/integrations/sync to re-run."
        ),
        configuration_data=row["configuration_data"],
    )


@router.post("/configure", response_model=DarwinboxConfigureResponse)
def configure_darwinbox(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> DarwinboxConfigureResponse:
    return _configure_impl(payload, background_tasks, session)


@hrms_router.post("/integrations", response_model=DarwinboxConfigureResponse)
def configure_darwinbox_alias(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> DarwinboxConfigureResponse:
    return _configure_impl(payload, background_tasks, session)
