from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.clickup.credentials import has_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import PmTokenConfigureResponse, PmTokenFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/project-management/clickup", tags=["integrations", "project-management", "clickup"])
pm_router = APIRouter(prefix="/project-management/clickup", tags=["integrations", "project-management", "clickup"])


def _mask(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("api_token", "clickup_token", "personal_token"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def _cfg(payload: ToolIntegrationPayload, session: Session) -> PmTokenConfigureResponse:
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
    ok = has_token(cfg)
    return PmTokenConfigureResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        token_configured=ok,
        next_step="Ready." if ok else "Set api_token (ClickUp personal token).",
        configuration_data=_mask(cfg),
    )


@router.post("/configure", response_model=PmTokenConfigureResponse)
def configure(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> PmTokenConfigureResponse:
    return _cfg(payload, session)


@pm_router.post("/integrations", response_model=PmTokenConfigureResponse)
def configure_a(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> PmTokenConfigureResponse:
    return _cfg(payload, session)


@router.get("/flow", response_model=PmTokenFlowResponse)
def flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> PmTokenFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    ok = has_token(cfg)
    return PmTokenFlowResponse(
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        token_configured=ok,
        next_step="Ready." if ok else "Add api_token.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return ToolIntegrationResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        configuration_data=_mask(cfg),
    )
