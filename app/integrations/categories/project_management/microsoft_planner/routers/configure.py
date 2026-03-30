"""Microsoft Graph Planner: configure, flow, status, refresh."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.microsoft_planner.credentials import has_graph_auth
from app.integrations.categories.project_management.microsoft_planner.token_refresh import ensure_graph_access_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    MicrosoftPlannerConfigureResponse,
    MicrosoftPlannerFlowResponse,
    MicrosoftPlannerRefreshTokensBody,
    MicrosoftPlannerRefreshTokensResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(
    prefix="/api/v1/integrations/project-management/microsoft-planner",
    tags=["integrations", "project-management", "microsoft-planner"],
)
pm_router = APIRouter(prefix="/project-management/microsoft-planner", tags=["integrations", "project-management", "microsoft-planner"])


def _mask(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("access_token", "refresh_token", "client_secret"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def _tool_row(row: dict[str, Any], *, configuration_data: dict | None = None) -> ToolIntegrationResponse:
    return ToolIntegrationResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        configuration_data=configuration_data if configuration_data is not None else row["configuration_data"],
    )


def _configure(payload: ToolIntegrationPayload, session: Session) -> MicrosoftPlannerConfigureResponse:
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
    masked = _mask(cfg)
    return MicrosoftPlannerConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        auth_configured=has_graph_auth(cfg),
        next_step="Call POST /refresh-tokens or set access_token; then GET /me or GET /plans with group_id.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=MicrosoftPlannerConfigureResponse)
def configure(payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)], session: Session = Depends(get_db)) -> MicrosoftPlannerConfigureResponse:
    return _configure(payload, session)


@pm_router.post("/integrations", response_model=MicrosoftPlannerConfigureResponse)
def configure_alias(payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)], session: Session = Depends(get_db)) -> MicrosoftPlannerConfigureResponse:
    return _configure(payload, session)


@router.post("/refresh-tokens", response_model=MicrosoftPlannerRefreshTokensResponse)
def refresh_tokens(body: MicrosoftPlannerRefreshTokensBody, session: Session = Depends(get_db)) -> MicrosoftPlannerRefreshTokensResponse:
    row = persistence.get_integration(session, body.org_id, body.tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    try:
        cfg, _, did = ensure_graph_access_token(session, row, force=body.force)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return MicrosoftPlannerRefreshTokensResponse(
        ok=True,
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        refreshed=did,
        message="Token refreshed." if did else "Token still valid.",
        configuration_data=_mask(cfg),
    )


@router.get("/flow", response_model=MicrosoftPlannerFlowResponse)
def flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> MicrosoftPlannerFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    ok = has_graph_auth(cfg)
    return MicrosoftPlannerFlowResponse(
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        auth_configured=ok,
        next_step="Ready." if ok else "Add tenant_id, client_id, client_secret (and optional refresh_token) or access_token.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _tool_row(row, configuration_data=_mask(cfg))
