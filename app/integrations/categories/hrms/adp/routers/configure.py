"""ADP: configure (OAuth 2.0 client credentials)."""

from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms._shared_routes import mask_configuration_data, tool_integration_response
from app.integrations.categories.hrms.adp import api_client
from app.integrations.categories.hrms.adp.credentials import (
    has_access_token,
    has_oauth_client,
    ready_for_api_calls,
    resolve_access_token,
    resolve_oauth_client,
    resolve_token_url,
)
from app.integrations.categories.hrms.adp.oauth import exchange_client_credentials, merge_token_into_config
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import AdpConfigureResponse, AdpFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/hrms/adp", tags=["integrations", "hrms", "adp"])

_SECRET_KEYS = ("access_token", "refresh_token", "client_secret", "adp_client_secret", "webhook_secret")


@router.post("/configure", response_model=AdpConfigureResponse)
def configure(payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)], session: Session = Depends(get_db)) -> AdpConfigureResponse:
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

    if has_oauth_client(cfg) and not cfg.get("skip_token_exchange"):
        try:
            cid, csec = resolve_oauth_client(cfg)
            token_url = resolve_token_url(cfg)
            scope = cfg.get("oauth_scope") or cfg.get("scope")
            token_payload = exchange_client_credentials(
                token_url=token_url,
                client_id=cid,
                client_secret=csec,
                scope=str(scope) if scope else None,
            )
            cfg = merge_token_into_config(cfg, token_payload)
            persistence.save_tool_integration_config(session, row["id"], cfg)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=400, detail=e.response.text[:2000]) from e
    elif not has_access_token(cfg):
        raise HTTPException(
            status_code=400,
            detail="Provide client_id/client_secret (ADP API Marketplace app) or access_token.",
        )

    token = resolve_access_token(cfg)
    if not token:
        raise HTTPException(status_code=400, detail="No access_token after configure.")

    ok = api_client.validate_connection(cfg, token)
    masked = mask_configuration_data(cfg, _SECRET_KEYS)

    return AdpConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="GET .../hrms/adp/employees when credentials_valid is true.",
        configuration_data=masked,
    )


@router.get("/flow", response_model=AdpFlowResponse)
def flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> AdpFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_api_calls(cfg):
        return AdpFlowResponse(
            organization_id=oid,
            tool_id=tid,
            ready_for_collection=False,
            next_step="Configure ADP OAuth client or access_token.",
        )
    token = resolve_access_token(cfg)
    assert token
    ok = api_client.validate_connection(cfg, token)
    return AdpFlowResponse(
        organization_id=oid,
        tool_id=tid,
        ready_for_collection=ok,
        next_step="Ready." if ok else "ADP /hr/v2/workers sample failed (check subscription and scopes).",
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
