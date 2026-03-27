"""Bitbucket Cloud: configure, flow, status."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.bitbucket.credentials import (
    oauth_complete,
    ready_for_collection,
    resolve_oauth_credentials,
    workspaces_selected,
)
from app.integrations.categories.devtools.bitbucket.oauth import build_authorization_url, build_state
from app.integrations.categories.devtools.bitbucket.seed_service import seed_bitbucket_evidence_masters
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    BitbucketConfigureResponse,
    BitbucketFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/devtools/bitbucket", tags=["integrations", "devtools", "bitbucket"])


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


def _configure_response(
    payload: ToolIntegrationPayload,
    session: Any,
) -> BitbucketConfigureResponse:
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
    seed_bitbucket_evidence_masters(session, payload.tool_id)

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg)

    oc = oauth_complete(cfg)
    ws = workspaces_selected(cfg)
    rdy = ready_for_collection(cfg)

    if rdy:
        return BitbucketConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            workspace_selection_required=False,
            ready_for_collection=True,
            authorization_url=None,
            state=None,
            next_step="Integration ready. POST /api/v1/evidence/collect or /api/v1/integrations/sync to pull evidence.",
            configuration_data=masked,
        )

    if oc and not ws:
        return BitbucketConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            workspace_selection_required=True,
            ready_for_collection=False,
            authorization_url=None,
            state=None,
            next_step="OAuth complete. GET .../devtools/bitbucket/workspaces then POST .../workspaces with workspace_slugs.",
            configuration_data=masked,
        )

    try:
        client_id, _s, redir = resolve_oauth_credentials(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(payload.org_id, payload.tool_id)
    auth_url = build_authorization_url(client_id=client_id, redirect_uri=redir, state=state)
    return BitbucketConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        workspace_selection_required=True,
        ready_for_collection=False,
        authorization_url=auth_url,
        state=state,
        next_step="Open authorization_url in a browser, approve Bitbucket access, then select workspaces to sync.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=BitbucketConfigureResponse)
def configure_bitbucket(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> BitbucketConfigureResponse:
    return _configure_response(payload, session)


@router.get("/flow", response_model=BitbucketFlowResponse)
def bitbucket_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> BitbucketFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    oc = oauth_complete(cfg)
    ws = workspaces_selected(cfg)
    rdy = ready_for_collection(cfg)
    redir = cfg.get("redirect_uri")

    if rdy:
        return BitbucketFlowResponse(
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            workspace_selection_required=False,
            ready_for_collection=True,
            redirect_uri=str(redir) if redir else None,
            next_step="Ready for evidence collection.",
            authorization_url=None,
            state=None,
        )

    if oc and not ws:
        return BitbucketFlowResponse(
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            workspace_selection_required=True,
            ready_for_collection=False,
            redirect_uri=str(redir) if redir else None,
            next_step="Select workspaces: GET .../workspaces then POST .../workspaces.",
            authorization_url=None,
            state=None,
        )

    try:
        client_id, _s, redir_resolved = resolve_oauth_credentials(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(org_id, tool_id)
    auth_url = build_authorization_url(client_id=client_id, redirect_uri=redir_resolved, state=state)
    return BitbucketFlowResponse(
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        workspace_selection_required=True,
        ready_for_collection=False,
        redirect_uri=str(redir_resolved),
        next_step="Complete OAuth via authorization_url, then select workspaces.",
        authorization_url=auth_url,
        state=state,
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
