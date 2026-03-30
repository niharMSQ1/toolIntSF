"""Azure DevOps: configure (PAT + organization + optional project)."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.azure_devops import api_client
from app.integrations.categories.devtools.azure_devops.credentials import (
    ready_for_api_calls,
    resolve_api_version,
    resolve_base_url,
    resolve_organization,
    resolve_pat,
)
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    AzureDevOpsConfigureResponse,
    AzureDevOpsFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/devtools/azure-devops", tags=["integrations", "devtools", "azure-devops"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("personal_access_token", "pat", "azure_devops_token", "access_token", "token", "webhook_secret"):
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


def _validate_pat(base_url: str, organization: str, pat: str, api_version: str) -> bool:
    try:
        api_client.list_projects(base_url, organization, pat, api_version=api_version, top=1)
        return True
    except httpx.HTTPStatusError:
        return False


@router.post("/configure", response_model=AzureDevOpsConfigureResponse)
def configure_azure_devops(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
) -> AzureDevOpsConfigureResponse:
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
            detail="Provide personal_access_token (or pat) and organization in configuration_data.",
        )

    pat = resolve_pat(cfg)
    assert pat
    org = resolve_organization(cfg)
    base_url = resolve_base_url(cfg)
    api_version = resolve_api_version(cfg)
    ok = _validate_pat(base_url, org, pat, api_version)

    return AzureDevOpsConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Call GET .../azure-devops/me or project-scoped routes when credentials_valid is true.",
        configuration_data=masked,
    )


@router.get("/flow", response_model=AzureDevOpsFlowResponse)
def azure_devops_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> AzureDevOpsFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    rdy = ready_for_api_calls(cfg)
    if not rdy:
        return AzureDevOpsFlowResponse(
            organization_id=oid,
            tool_id=tid,
            ready_for_collection=False,
            next_step="Set PAT and organization via POST .../configure.",
        )
    pat = resolve_pat(cfg)
    org = resolve_organization(cfg)
    base_url = resolve_base_url(cfg)
    api_version = resolve_api_version(cfg)
    assert pat
    ok = _validate_pat(base_url, org, pat, api_version)
    return AzureDevOpsFlowResponse(
        organization_id=oid,
        tool_id=tid,
        ready_for_collection=ok,
        next_step="Ready for API calls." if ok else "PAT or organization appears invalid.",
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
