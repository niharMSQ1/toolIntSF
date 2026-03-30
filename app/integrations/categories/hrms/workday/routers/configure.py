"""Workday: configure (OAuth 2.0 client credentials and/or stored access token)."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.workday import api_client
from app.integrations.categories.hrms.workday.credentials import (
    has_access_token,
    has_oauth_client,
    ready_for_api_calls,
    resolve_access_token,
    resolve_api_version,
    resolve_hostname,
    resolve_oauth_client,
    resolve_tenant,
)
from app.integrations.categories.hrms.workday.oauth import exchange_client_credentials, merge_token_response_into_config
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import ToolIntegrationPayload, ToolIntegrationResponse, WorkdayConfigureResponse, WorkdayFlowResponse

router = APIRouter(prefix="/api/v1/integrations/hrms/workday", tags=["integrations", "hrms", "workday"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("access_token", "refresh_token", "client_secret", "workday_client_secret", "webhook_secret"):
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


@router.post("/configure", response_model=WorkdayConfigureResponse)
def configure_workday(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> WorkdayConfigureResponse:
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
    cfg = dict(row["configuration_data"])
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")

    oid = str(row["organization_id"])
    tid = str(row["tool_id"])

    try:
        resolve_hostname(cfg)
        resolve_tenant(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if has_oauth_client(cfg) and not cfg.get("skip_token_exchange"):
        try:
            cid, csec = resolve_oauth_client(cfg)
            hostname = resolve_hostname(cfg)
            tenant = resolve_tenant(cfg)
            scope = cfg.get("oauth_scope") or cfg.get("scope")
            token_payload = exchange_client_credentials(
                hostname=hostname,
                tenant=tenant,
                client_id=cid,
                client_secret=csec,
                scope=str(scope) if scope else None,
            )
            cfg = merge_token_response_into_config(cfg, token_payload)
            persistence.save_tool_integration_config(session, row["id"], cfg)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=400, detail=f"Workday token exchange failed: {e.response.text[:2000]}") from e
    elif not has_access_token(cfg):
        raise HTTPException(
            status_code=400,
            detail="Provide OAuth client_id/client_secret or a pre-issued access_token with workday_hostname and workday_tenant.",
        )

    token = resolve_access_token(cfg)
    if not token:
        raise HTTPException(status_code=400, detail="No access_token after configure.")

    ok = api_client.validate_token_with_workers(cfg, token)
    masked = _mask_configuration_data(cfg)

    return WorkdayConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Call GET .../hrms/workday/employees when credentials_valid is true.",
        configuration_data=masked,
    )


@router.get("/flow", response_model=WorkdayFlowResponse)
def workday_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> WorkdayFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_api_calls(cfg):
        return WorkdayFlowResponse(
            organization_id=oid,
            tool_id=tid,
            ready_for_collection=False,
            api_version=resolve_api_version(cfg),
            next_step="Configure workday_hostname, workday_tenant, and OAuth client or access_token.",
        )
    token = resolve_access_token(cfg)
    assert token
    ok = api_client.validate_token_with_workers(cfg, token)
    return WorkdayFlowResponse(
        organization_id=oid,
        tool_id=tid,
        ready_for_collection=ok,
        api_version=resolve_api_version(cfg),
        next_step="Ready for Workday REST calls." if ok else "Token invalid or missing Workers API permission.",
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
