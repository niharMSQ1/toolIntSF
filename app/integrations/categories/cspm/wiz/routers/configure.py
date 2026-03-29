"""Wiz CSPM: configure, flow, status (service account + GraphQL URL)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.cspm.wiz.credentials import (
    has_access_token,
    ready_for_collection,
    resolve_graphql_url,
)
from app.integrations.categories.cspm.wiz.collection_runner import run_wiz_evidence_collection_after_configure_background
from app.integrations.categories.cspm.wiz.token_refresh import force_refresh_access_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    ToolIntegrationPayload,
    ToolIntegrationResponse,
    WizConfigureResponse,
    WizFlowResponse,
    WizRefreshTokensResponse,
    ZohoRefreshTokensBody,
)

router = APIRouter(prefix="/api/v1/integrations/cspm/wiz", tags=["integrations", "cspm", "wiz"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("access_token", "refresh_token", "client_secret"):
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


@router.post("/configure", response_model=WizConfigureResponse)
def configure_wiz(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> WizConfigureResponse:
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
    try:
        row_after = persistence.get_integration(session, payload.org_id, payload.tool_id)
        if not row_after:
            raise HTTPException(status_code=500, detail="Integration row missing after upsert.")
        new_cfg = force_refresh_access_token(session, row_after)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Wiz token exchange failed: {e}") from e

    if not isinstance(new_cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(new_cfg)
    rdy = ready_for_collection(new_cfg)

    if rdy:
        background_tasks.add_task(
            run_wiz_evidence_collection_after_configure_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )

    return WizConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=has_access_token(new_cfg),
        ready_for_collection=rdy,
        collection_started_in_background=rdy,
        next_step=(
            "Integration ready. Full Wiz evidence collection has been started in the background; "
            "no separate POST to /evidence/wiz/collect is required."
            if rdy
            else "Fix configuration and POST /configure again."
        ),
        configuration_data=masked,
    )


@router.get("/flow", response_model=WizFlowResponse)
def wiz_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> WizFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    try:
        resolve_graphql_url(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    ok = ready_for_collection(cfg)
    return WizFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=has_access_token(cfg),
        ready_for_collection=ok,
        next_step=(
            "Ready for collection."
            if ok
            else "Set graphql_url, client_id, client_secret in configuration_data and POST /configure."
        ),
    )


@router.post("/refresh-tokens", response_model=WizRefreshTokensResponse)
def wiz_refresh_tokens(payload: ZohoRefreshTokensBody, session: Session = Depends(get_db)) -> WizRefreshTokensResponse:
    """Exchange client credentials for a new access token (same as configure)."""
    row = persistence.get_integration(session, payload.org_id, payload.tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    try:
        new_cfg = force_refresh_access_token(session, row)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e)) from e
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(new_cfg if isinstance(new_cfg, dict) else {})
    return WizRefreshTokensResponse(
        ok=True,
        organization_id=oid,
        tool_id=tid,
        refreshed=True,
        message="Access token refreshed from Wiz auth (client credentials).",
        configuration_data=masked,
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
