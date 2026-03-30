"""Asana: configure, flow, status, token refresh."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.asana.credentials import (
    has_bearer_token,
    resolve_oauth_credentials,
    resolve_redirect_uri,
)
from app.integrations.categories.project_management.asana.oauth import build_authorization_url, build_state
from app.integrations.categories.project_management.asana.token_refresh import refresh_asana_access_tokens
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    AsanaConfigureResponse,
    AsanaFlowResponse,
    AsanaRefreshTokensBody,
    AsanaRefreshTokensResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(
    prefix="/api/v1/integrations/project-management/asana",
    tags=["integrations", "project-management", "asana"],
)
pm_router = APIRouter(prefix="/project-management/asana", tags=["integrations", "project-management", "asana"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in (
        "access_token",
        "refresh_token",
        "client_secret",
        "personal_access_token",
        "webhook_secret",
    ):
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


def _configure_asana_response(payload: ToolIntegrationPayload, session: Session) -> AsanaConfigureResponse:
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

    if has_bearer_token(cfg):
        auth_method = "pat" if (cfg.get("personal_access_token") and str(cfg["personal_access_token"]).strip()) else "oauth"
        return AsanaConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            auth_method=auth_method,
            authorization_url=None,
            state=None,
            next_step="Bearer token present. Call GET .../me or GET .../workspaces to verify API access.",
            configuration_data=masked,
        )

    try:
        client_id, _secret = resolve_oauth_credentials(cfg)
        redir = resolve_redirect_uri(cfg)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
            + " Alternatively set personal_access_token for a single-user integration.",
        ) from e
    state = build_state(payload.org_id, payload.tool_id)
    auth_url = build_authorization_url(client_id=client_id, redirect_uri=redir, state=state)
    return AsanaConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        auth_method="oauth",
        authorization_url=auth_url,
        state=state,
        next_step="Open authorization_url in a browser and approve access, then complete the OAuth callback.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=AsanaConfigureResponse)
def configure_asana(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> AsanaConfigureResponse:
    return _configure_asana_response(payload, session)


@pm_router.post("/integrations", response_model=AsanaConfigureResponse)
def configure_asana_alias(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
) -> AsanaConfigureResponse:
    return _configure_asana_response(payload, session)


@router.post("/refresh-tokens", response_model=AsanaRefreshTokensResponse)
def asana_refresh_tokens(
    payload: AsanaRefreshTokensBody,
    session: Session = Depends(get_db),
) -> AsanaRefreshTokensResponse:
    row = persistence.get_integration(session, payload.org_id, payload.tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    try:
        cfg, did_refresh = refresh_asana_access_tokens(session, row, force=payload.force)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg)
    msg = (
        "Access token refreshed from Asana."
        if did_refresh
        else "Access token still valid; Asana token API was not called. Use force=true to refresh anyway."
    )
    return AsanaRefreshTokensResponse(
        ok=True,
        organization_id=oid,
        tool_id=tid,
        refreshed=did_refresh,
        message=msg,
        configuration_data=masked,
    )


@router.get("/flow", response_model=AsanaFlowResponse)
def asana_flow_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> AsanaFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    try:
        redirect = resolve_redirect_uri(cfg)
    except ValueError:
        redirect = cfg.get("redirect_uri")
        if redirect is not None:
            redirect = str(redirect)
    has_token = has_bearer_token(cfg)

    if has_token:
        auth_method = "pat" if (cfg.get("personal_access_token") and str(cfg["personal_access_token"]).strip()) else "oauth"
        return AsanaFlowResponse(
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            auth_method=auth_method,
            redirect_uri=redirect,
            next_step="API authentication is ready. Use project-management data routes.",
            authorization_url=None,
            state=None,
        )

    try:
        client_id, _secret = resolve_oauth_credentials(cfg)
        redir = resolve_redirect_uri(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(org_id, tool_id)
    auth_url = build_authorization_url(client_id=client_id, redirect_uri=redir, state=state)
    return AsanaFlowResponse(
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        auth_method="oauth",
        redirect_uri=redir,
        next_step="Open authorization_url in a browser and approve Asana access.",
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
