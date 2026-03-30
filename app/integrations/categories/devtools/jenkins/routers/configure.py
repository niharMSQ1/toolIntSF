"""Jenkins: configure (base URL + user + API token)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.jenkins import api_client
from app.integrations.categories.devtools.jenkins.credentials import (
    ready_for_api_calls,
    resolve_api_token,
    resolve_base_url,
    resolve_username,
)
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    JenkinsConfigureResponse,
    JenkinsFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/devtools/jenkins", tags=["integrations", "devtools", "jenkins"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("api_token", "jenkins_token", "token", "password", "webhook_secret"):
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


@router.post("/configure", response_model=JenkinsConfigureResponse)
def configure_jenkins(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> JenkinsConfigureResponse:
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
            detail="Provide jenkins_url, username, and api_token (or jenkins_token) in configuration_data.",
        )

    token = resolve_api_token(cfg)
    assert token
    base_url = resolve_base_url(cfg)
    username = resolve_username(cfg)
    ok = api_client.validate_connection(base_url, username, token)

    return JenkinsConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Call GET .../jenkins/me and job-scoped routes with job_path (folder segments allowed).",
        configuration_data=masked,
    )


@router.get("/flow", response_model=JenkinsFlowResponse)
def jenkins_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> JenkinsFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_api_calls(cfg):
        return JenkinsFlowResponse(
            organization_id=oid,
            tool_id=tid,
            ready_for_collection=False,
            next_step="Set jenkins_url, username, and api_token via POST .../configure.",
        )
    token = resolve_api_token(cfg)
    base_url = resolve_base_url(cfg)
    username = resolve_username(cfg)
    assert token
    ok = api_client.validate_connection(base_url, username, token)
    return JenkinsFlowResponse(
        organization_id=oid,
        tool_id=tid,
        ready_for_collection=ok,
        next_step="Ready for Jenkins JSON API calls." if ok else "Credentials failed Jenkins /api/json check.",
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
