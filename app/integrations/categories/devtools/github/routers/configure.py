"""GitHub: configure (PAT or OAuth app), flow, status."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.github.credentials import (
    oauth_app_configured,
    ready_for_api_calls,
    resolve_oauth_credentials,
    resolve_redirect_uri,
)
from app.integrations.categories.devtools.github.oauth import build_authorization_url, build_state
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    GitHubConfigureResponse,
    GitHubFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/devtools/github", tags=["integrations", "devtools", "github"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("access_token", "personal_access_token", "github_token", "token", "client_secret", "webhook_secret"):
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


def _configure_response(payload: ToolIntegrationPayload, session: Any) -> GitHubConfigureResponse:
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

    rdy = ready_for_api_calls(cfg)
    if rdy:
        return GitHubConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            ready_for_collection=True,
            authorization_url=None,
            state=None,
            next_step="Integration ready. Call GET .../devtools/github/me or repo-scoped routes with owner/repo.",
            configuration_data=masked,
        )

    if not oauth_app_configured(cfg):
        raise HTTPException(
            status_code=400,
            detail="Provide personal_access_token (or access_token) in configuration_data, "
            "or OAuth app fields: client_id, client_secret, redirect_uri.",
        )

    client_id, _sec = resolve_oauth_credentials(cfg)
    redir = resolve_redirect_uri(cfg)
    state = build_state(payload.org_id, payload.tool_id)
    auth_url = build_authorization_url(client_id=client_id, redirect_uri=redir, state=state)
    return GitHubConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        ready_for_collection=False,
        authorization_url=auth_url,
        state=state,
        next_step="Open authorization_url in a browser, approve GitHub access; callback stores access_token.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=GitHubConfigureResponse)
def configure_github(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> GitHubConfigureResponse:
    return _configure_response(payload, session)


@router.get("/flow", response_model=GitHubFlowResponse)
def github_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> GitHubFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    rdy = ready_for_api_calls(cfg)

    if rdy:
        return GitHubFlowResponse(
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            ready_for_collection=True,
            redirect_uri=cfg.get("redirect_uri") if isinstance(cfg.get("redirect_uri"), str) else None,
            next_step="Ready for API calls.",
            authorization_url=None,
            state=None,
        )

    if not oauth_app_configured(cfg):
        raise HTTPException(
            status_code=400,
            detail="Configure personal_access_token or OAuth app (client_id, client_secret, redirect_uri).",
        )

    client_id, _sec = resolve_oauth_credentials(cfg)
    redir = resolve_redirect_uri(cfg)
    state = build_state(org_id, tool_id)
    auth_url = build_authorization_url(client_id=client_id, redirect_uri=redir, state=state)
    return GitHubFlowResponse(
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        ready_for_collection=False,
        redirect_uri=redir,
        next_step="Complete OAuth via authorization_url.",
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
