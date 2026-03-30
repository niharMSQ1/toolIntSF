"""SailPoint IdentityNow: configure, flow, status."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.sailpoint.collection_runner import (
    run_sailpoint_evidence_collection_after_configure_background,
    validate_sailpoint_credentials,
)
from app.integrations.categories.idp.sailpoint.credentials import (
    has_access_token,
    has_oauth_client,
    ready_for_collection,
    resolve_access_token,
    resolve_api_base,
    resolve_oauth_client,
)
from app.integrations.categories.idp.sailpoint.oauth import exchange_client_credentials, merge_token_into_config
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import SailPointConfigureResponse, SailPointFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/sailpoint-identity", tags=["integrations", "idp", "sailpoint"])
idp_router = APIRouter(prefix="/idp/sailpoint-identity", tags=["integrations", "idp", "sailpoint"])


def _mask(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("access_token", "client_secret", "sailpoint_client_secret", "refresh_token"):
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


def _configure(
    payload: ToolIntegrationPayload,
    session: Session,
    background_tasks: BackgroundTasks,
) -> SailPointConfigureResponse:
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
    oid, tid = str(row["organization_id"]), str(row["tool_id"])
    masked = _mask(cfg)

    if not ready_for_collection(cfg):
        return SailPointConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Set sailpoint_base_url and OAuth client_id/client_secret.",
            configuration_data=masked,
        )

    if has_oauth_client(cfg) and not cfg.get("skip_token_exchange"):
        try:
            cid, csec = resolve_oauth_client(cfg)
            base = resolve_api_base(cfg)
            token_payload = exchange_client_credentials(api_base=base, client_id=cid, client_secret=csec)
            cfg = merge_token_into_config(cfg, token_payload)
            persistence.save_tool_integration_config(session, row["id"], cfg)
            masked = _mask(cfg)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=400, detail=e.response.text[:2000]) from e
    elif not has_access_token(cfg):
        raise HTTPException(
            status_code=400,
            detail="Provide client_id/client_secret or access_token with skip_token_exchange.",
        )

    if not validate_sailpoint_credentials(cfg):
        return SailPointConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Public identities request failed; check API roles and sailpoint_identities_path.",
            configuration_data=masked,
        )

    background_tasks.add_task(
        run_sailpoint_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return SailPointConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=True,
        ready_for_collection=True,
        collection_started_in_background=True,
        next_step="SailPoint credentials valid. IAM evidence collection running in background.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=SailPointConfigureResponse)
def configure_sailpoint(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> SailPointConfigureResponse:
    return _configure(payload, session, background_tasks)


@idp_router.post("/integrations", response_model=SailPointConfigureResponse)
def configure_sailpoint_idp(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> SailPointConfigureResponse:
    return _configure(payload, session, background_tasks)


@router.get("/flow", response_model=SailPointFlowResponse)
def sailpoint_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> SailPointFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid, tid = str(row["organization_id"]), str(row["tool_id"])
    if not ready_for_collection(cfg):
        return SailPointFlowResponse(
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            next_step="Configure sailpoint_base_url and OAuth client.",
        )
    ok = bool(resolve_access_token(cfg)) and validate_sailpoint_credentials(cfg)
    return SailPointFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Ready." if ok else "Token present but API validation failed.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def sailpoint_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _tool_row(row, configuration_data=_mask(cfg))
