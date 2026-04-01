"""Google Workspace: configure (OAuth refresh), flow, status."""

from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.google_workspace.collection_runner import (
    run_google_workspace_evidence_collection_after_configure_background,
    validate_google_workspace_credentials,
)
from app.integrations.categories.idp.google_workspace.credentials import (
    has_refresh_flow,
    ready_for_collection,
    resolve_access_token,
    resolve_oauth_client,
    resolve_refresh_token,
    resolve_workspace_domain,
)
from app.integrations.categories.idp.google_workspace.oauth import merge_token_into_config, refresh_access_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import GoogleWorkspaceConfigureResponse, GoogleWorkspaceFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/google-workspace", tags=["integrations", "idp", "google_workspace"])
idp_router = APIRouter(prefix="/idp/google-workspace", tags=["integrations", "idp", "google_workspace"])


def _mask(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("access_token", "refresh_token", "client_secret", "google_client_secret"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def _row(r: dict[str, Any], *, configuration_data: dict | None = None) -> ToolIntegrationResponse:
    return ToolIntegrationResponse(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        tool_id=str(r["tool_id"]),
        configuration_data=configuration_data if configuration_data is not None else r["configuration_data"],
    )


def _configure(
    payload: ToolIntegrationPayload,
    session: Session,
    background_tasks: BackgroundTasks,
) -> GoogleWorkspaceConfigureResponse:
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
        return GoogleWorkspaceConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Set google_workspace_domain and OAuth client + refresh_token or access_token.",
            configuration_data=masked,
        )

    try:
        resolve_workspace_domain(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if has_refresh_flow(cfg) and not cfg.get("skip_token_exchange"):
        try:
            cid, csec = resolve_oauth_client(cfg)
            rt = resolve_refresh_token(cfg)
            assert rt
            token_payload = refresh_access_token(client_id=cid, client_secret=csec, refresh_token=rt)
            cfg = merge_token_into_config(cfg, token_payload)
            persistence.save_tool_integration_config(session, row["id"], cfg)
            masked = _mask(cfg)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=400, detail=e.response.text[:2000]) from e
    elif not resolve_access_token(cfg):
        raise HTTPException(
            status_code=400,
            detail="Provide refresh_token + client_id/client_secret, or access_token with skip_token_exchange.",
        )

    if not validate_google_workspace_credentials(cfg):
        return GoogleWorkspaceConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Directory API users.list failed; enable Admin SDK scope admin.directory.user.readonly.",
            configuration_data=masked,
        )

    background_tasks.add_task(
        run_google_workspace_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return GoogleWorkspaceConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=True,
        ready_for_collection=True,
        collection_started_in_background=True,
        next_step="Google Workspace valid. IAM evidence collection running in background.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=GoogleWorkspaceConfigureResponse)
def configure_google(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> GoogleWorkspaceConfigureResponse:
    return _configure(payload, session, background_tasks)


@idp_router.post("/integrations", response_model=GoogleWorkspaceConfigureResponse)
def configure_google_idp(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> GoogleWorkspaceConfigureResponse:
    return _configure(payload, session, background_tasks)


@router.get("/flow", response_model=GoogleWorkspaceFlowResponse)
def google_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> GoogleWorkspaceFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid, tid = str(row["organization_id"]), str(row["tool_id"])
    if not ready_for_collection(cfg):
        return GoogleWorkspaceFlowResponse(
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            next_step="Configure domain and OAuth.",
        )
    ok = bool(resolve_access_token(cfg)) and validate_google_workspace_credentials(cfg)
    return GoogleWorkspaceFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Ready." if ok else "Token invalid for Directory API.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def google_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _row(row, configuration_data=_mask(cfg))
