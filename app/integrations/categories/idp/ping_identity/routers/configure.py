"""Ping Identity (PingOne Platform): configure, flow, status."""

from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.ping_identity.collection_runner import (
    run_ping_identity_evidence_collection_after_configure_background,
    validate_ping_credentials,
)
from app.integrations.categories.idp.ping_identity.credentials import (
    has_access_token,
    has_oauth_client,
    ready_for_collection,
    resolve_access_token,
    resolve_auth_base,
    resolve_oauth_client,
    resolve_token_environment_id,
)
from app.integrations.categories.idp.ping_identity.oauth import exchange_client_credentials, merge_token_into_config
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import PingIdentityConfigureResponse, PingIdentityFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/ping-identity", tags=["integrations", "idp", "ping_identity"])
idp_router = APIRouter(prefix="/idp/ping-identity", tags=["integrations", "idp", "ping_identity"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("access_token", "client_secret", "pingone_client_secret", "refresh_token"):
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
    session: Session,
    background_tasks: BackgroundTasks,
) -> PingIdentityConfigureResponse:
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

    if not ready_for_collection(cfg):
        return PingIdentityConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step=(
                "Set pingone_environment_id, client_id, and client_secret (PingOne Worker app), "
                "then POST /configure again."
            ),
            configuration_data=masked,
        )

    if has_oauth_client(cfg) and not cfg.get("skip_token_exchange"):
        try:
            cid, csec = resolve_oauth_client(cfg)
            auth_base = resolve_auth_base(cfg)
            token_env = resolve_token_environment_id(cfg)
            scope = cfg.get("oauth_scope") or cfg.get("scope")
            token_payload = exchange_client_credentials(
                auth_base=auth_base,
                token_environment_id=token_env,
                client_id=cid,
                client_secret=csec,
                scope=str(scope) if scope else None,
            )
            cfg = merge_token_into_config(cfg, token_payload)
            persistence.save_tool_integration_config(session, row["id"], cfg)
            masked = _mask_configuration_data(cfg)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=400, detail=e.response.text[:2000]) from e
    elif not has_access_token(cfg):
        raise HTTPException(
            status_code=400,
            detail="Provide client_id/client_secret for token exchange or access_token with skip_token_exchange.",
        )

    if not validate_ping_credentials(cfg):
        return PingIdentityConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Could not list users (GET .../environments/{envID}/users). Check Worker roles and environment ID.",
            configuration_data=masked,
        )

    background_tasks.add_task(
        run_ping_identity_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return PingIdentityConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=True,
        ready_for_collection=True,
        collection_started_in_background=True,
        next_step="PingOne credentials valid. IAM evidence collection is running in the background.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=PingIdentityConfigureResponse)
def configure_ping_identity(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> PingIdentityConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@idp_router.post("/configure", response_model=PingIdentityConfigureResponse)
def configure_ping_identity_alias(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> PingIdentityConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@idp_router.post("/integrations", response_model=PingIdentityConfigureResponse)
def configure_ping_identity_idp_integrations_alias(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> PingIdentityConfigureResponse:
    """Alias matching Okta `/idp/okta/integrations` naming."""
    return _configure_response(payload, session, background_tasks)


@router.get("/flow", response_model=PingIdentityFlowResponse)
def ping_identity_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> PingIdentityFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_collection(cfg):
        return PingIdentityFlowResponse(
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            next_step="Configure PingOne Worker app credentials and pingone_environment_id.",
        )
    token = resolve_access_token(cfg)
    ok = bool(token) and validate_ping_credentials(cfg)
    return PingIdentityFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Ready." if ok else "Token present but sample user list failed; check roles.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def ping_identity_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _tool_integration_response(row, configuration_data=_mask_configuration_data(cfg))
