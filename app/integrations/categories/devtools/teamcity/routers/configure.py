"""TeamCity: configure (server URL + access token)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.teamcity import api_client
from app.integrations.categories.devtools.teamcity.credentials import has_token, ready_for_api_calls, resolve_base_url, resolve_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import TeamCityConfigureResponse, TeamCityFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/devtools/teamcity", tags=["integrations", "devtools", "teamcity"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("teamcity_token", "token", "access_token", "webhook_secret"):
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


@router.post("/configure", response_model=TeamCityConfigureResponse)
def configure_teamcity(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> TeamCityConfigureResponse:
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

    if not ready_for_api_calls(cfg):
        raise HTTPException(
            status_code=400,
            detail="Provide teamcity_base_url and teamcity_token (or token) in configuration_data.",
        )

    token = resolve_token(cfg)
    base_url = resolve_base_url(cfg)
    assert token
    ok = api_client.validate_connection(base_url, token)

    return TeamCityConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Call GET .../teamcity/me, /projects, /builds.",
        configuration_data=masked,
    )


@router.get("/flow", response_model=TeamCityFlowResponse)
def teamcity_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> TeamCityFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not has_token(cfg):
        return TeamCityFlowResponse(
            organization_id=oid,
            tool_id=tid,
            ready_for_collection=False,
            next_step="Add teamcity_token and teamcity_base_url.",
        )
    token = resolve_token(cfg)
    try:
        base_url = resolve_base_url(cfg)
    except ValueError as e:
        return TeamCityFlowResponse(organization_id=oid, tool_id=tid, ready_for_collection=False, next_step=str(e))
    assert token
    ok = api_client.validate_connection(base_url, token)
    return TeamCityFlowResponse(
        organization_id=oid,
        tool_id=tid,
        ready_for_collection=ok,
        next_step="Ready." if ok else "Token rejected by /app/rest/server.",
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
