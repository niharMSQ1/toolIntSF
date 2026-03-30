"""Rippling: Bearer API key or access_token + API base."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms._shared_routes import mask_configuration_data, tool_integration_response
from app.integrations.categories.hrms.rippling import api_client
from app.integrations.categories.hrms.rippling.credentials import ready_for_api_calls, resolve_bearer_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import RipplingConfigureResponse, RipplingFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

logger = logging.getLogger("app.integrations.rippling")

router = APIRouter(prefix="/api/v1/integrations/hrms/rippling", tags=["integrations", "hrms", "rippling"])

_SECRET_KEYS = ("access_token", "rippling_api_key", "api_key", "webhook_secret")


@router.post("/configure", response_model=RipplingConfigureResponse)
def configure(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> RipplingConfigureResponse:
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

    token = resolve_bearer_token(cfg)
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Provide access_token or rippling_api_key (and optional rippling_api_base).",
        )

    ok = False
    try:
        ok = api_client.validate_connection(cfg, token)
    except httpx.HTTPStatusError as e:
        logger.warning("Rippling validation HTTP error: %s", e.response.status_code)
        raise HTTPException(status_code=400, detail=e.response.text[:2000]) from e

    masked = mask_configuration_data(cfg, _SECRET_KEYS)

    return RipplingConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="GET .../hrms/rippling/employees when credentials_valid is true.",
        configuration_data=masked,
    )


@router.get("/flow", response_model=RipplingFlowResponse)
def flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> RipplingFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_api_calls(cfg):
        return RipplingFlowResponse(
            organization_id=oid,
            tool_id=tid,
            ready_for_collection=False,
            next_step="Configure rippling_api_key or access_token.",
        )
    token = resolve_bearer_token(cfg)
    assert token
    try:
        ok = api_client.validate_connection(cfg, token)
    except httpx.HTTPStatusError:
        ok = False
    return RipplingFlowResponse(
        organization_id=oid,
        tool_id=tid,
        ready_for_collection=ok,
        next_step="Ready." if ok else "Rippling employees sample failed; check rippling_employees_path.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return tool_integration_response(row, configuration_data=mask_configuration_data(cfg, _SECRET_KEYS))
