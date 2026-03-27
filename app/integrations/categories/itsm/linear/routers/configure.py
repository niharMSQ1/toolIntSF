"""Linear: configure, flow, status, token refresh (ITSM category)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.itsm.linear.collection_runner import (
    run_linear_evidence_collection_after_oauth_background,
)
from app.integrations.categories.itsm.linear.credentials import (
    has_access_token,
    resolve_oauth_credentials,
    resolve_redirect_uri,
)
from app.integrations.categories.itsm.linear.oauth import build_authorization_url, build_state
from app.integrations.categories.itsm.linear.seed_service import seed_linear_evidence_masters
from app.integrations.categories.itsm.linear.token_refresh import refresh_linear_access_tokens
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    LinearConfigureResponse,
    LinearFlowResponse,
    LinearRefreshTokensBody,
    LinearRefreshTokensResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/linear", tags=["integrations", "itsm", "linear"])
itsm_router = APIRouter(prefix="/itsm/linear", tags=["integrations", "itsm", "linear"])


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


def _configure_linear_response(
    payload: ToolIntegrationPayload,
    session: Session,
    background_tasks: BackgroundTasks,
) -> LinearConfigureResponse:
    existing = persistence.get_integration(session, payload.org_id, payload.tool_id)
    data: dict[str, Any] = {}
    if existing:
        existing_cfg = existing.get("configuration_data")
        if isinstance(existing_cfg, dict):
            data.update(existing_cfg)
    data.update(dict(payload.configuration_data))
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
    seed_linear_evidence_masters(session, payload.tool_id)

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg)

    if has_access_token(cfg):
        background_tasks.add_task(
            run_linear_evidence_collection_after_oauth_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )
        return LinearConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            authorization_url=None,
            state=None,
            next_step=(
                "OAuth tokens already on this integration. Evidence collection has been started in the background. "
                "No further action is required."
            ),
            configuration_data=masked,
        )

    try:
        client_id, _secret = resolve_oauth_credentials(cfg)
        redir = resolve_redirect_uri(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(payload.org_id, payload.tool_id)
    auth_url = build_authorization_url(
        client_id=client_id,
        redirect_uri=redir,
        state=state,
    )
    return LinearConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        authorization_url=auth_url,
        state=state,
        next_step=(
            "Open authorization_url in a browser and approve access. After redirect, evidence collection runs "
            "automatically in the background (no separate POST to /api/v1/evidence/linear/collect required)."
        ),
        configuration_data=masked,
    )


@router.post("/refresh-tokens", response_model=LinearRefreshTokensResponse)
def linear_refresh_tokens(
    payload: LinearRefreshTokensBody,
    session: Session = Depends(get_db),
) -> LinearRefreshTokensResponse:
    row = persistence.get_integration(session, payload.org_id, payload.tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    try:
        cfg, did_refresh = refresh_linear_access_tokens(session, row, force=payload.force)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg)
    msg = (
        "Access token refreshed from Linear."
        if did_refresh
        else "Access token still valid; Linear token API was not called. Use force=true to refresh anyway."
    )
    return LinearRefreshTokensResponse(
        ok=True,
        organization_id=oid,
        tool_id=tid,
        refreshed=did_refresh,
        message=msg,
        configuration_data=masked,
    )


@router.post("/configure", response_model=LinearConfigureResponse)
def configure_linear(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> LinearConfigureResponse:
    return _configure_linear_response(payload, session, background_tasks)


@itsm_router.post("/integrations", response_model=LinearConfigureResponse)
def configure_linear_itsm_alias(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> LinearConfigureResponse:
    return _configure_linear_response(payload, session, background_tasks)


@router.get("/flow", response_model=LinearFlowResponse)
def linear_flow_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> LinearFlowResponse:
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
    has_token = has_access_token(cfg)

    if has_token:
        return LinearFlowResponse(
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            redirect_uri=redirect,
            next_step=(
                "OAuth is complete. Evidence collection runs automatically after the OAuth redirect "
                "(or is already in progress). No separate API call is required."
            ),
            collect_post_json_example=None,
        )

    try:
        client_id, _secret = resolve_oauth_credentials(cfg)
        redir = resolve_redirect_uri(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(org_id, tool_id)
    auth_url = build_authorization_url(
        client_id=client_id,
        redirect_uri=redir,
        state=state,
    )
    return LinearFlowResponse(
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        redirect_uri=redirect,
        next_step=(
            "Open authorization_url in a browser, approve Linear access. "
            "You must be redirected to redirect_uri on THIS FastAPI host (same port as uvicorn). "
            "If your redirect_uri does not match the Linear app callback URL, update the app "
            "and POST /configure with matching redirect_uri."
        ),
        authorization_url=auth_url,
        state=state,
        collect_post_json_example=None,
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
