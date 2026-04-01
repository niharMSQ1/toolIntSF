"""Monday: configure, flow, status."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.monday.credentials import has_api_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    MondayConfigureResponse,
    MondayFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(
    prefix="/api/v1/integrations/project-management/monday",
    tags=["integrations", "project-management", "monday"],
)
pm_router = APIRouter(prefix="/project-management/monday", tags=["integrations", "project-management", "monday"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("api_token", "monday_api_token", "personal_api_token"):
        if k in masked and masked[k]:
            masked[k] = "***"
    return masked


def _tool_integration_response(
    row: dict[str, Any],
    *,
    configuration_data: dict | None = None,
) -> ToolIntegrationResponse:
    return ToolIntegrationResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        configuration_data=configuration_data if configuration_data is not None else row["configuration_data"],
    )


def _configure_response(payload: ToolIntegrationPayload, session: Session) -> MondayConfigureResponse:
    data = dict(payload.configuration_data)
    try:
        row = persistence.upsert_tool_integration(
            session,
            org_id=payload.org_id,
            tool_id=payload.tool_id,
            user_id=payload.user_id,
            configuration_data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg)

    if has_api_token(cfg):
        return MondayConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            token_configured=True,
            next_step="API token saved. Call GET .../me to verify.",
            configuration_data=masked,
        )
    return MondayConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        token_configured=False,
        next_step="Set api_token (or monday_api_token) in configuration_data — see Monday Developer Center.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=MondayConfigureResponse)
def configure_monday(payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)], session: Session = Depends(get_db)) -> MondayConfigureResponse:
    return _configure_response(payload, session)


@pm_router.post("/integrations", response_model=MondayConfigureResponse)
def configure_monday_alias(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
) -> MondayConfigureResponse:
    return _configure_response(payload, session)


@router.get("/flow", response_model=MondayFlowResponse)
def monday_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> MondayFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    ok = has_api_token(cfg)
    return MondayFlowResponse(
        organization_id=oid,
        tool_id=tid,
        token_configured=ok,
        next_step="Ready for API calls." if ok else "Add api_token to configuration_data.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def integration_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    masked = _mask_configuration_data(cfg)
    return _tool_integration_response(row, configuration_data=masked)
