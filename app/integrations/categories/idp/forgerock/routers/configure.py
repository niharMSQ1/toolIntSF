"""ForgeRock: configure, flow, status."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.forgerock.collection_runner import (
    run_forgerock_evidence_collection_after_configure_background,
    validate_forgerock_credentials,
)
from app.integrations.categories.idp.forgerock.credentials import (
    has_access_token,
    has_oauth_client,
    ready_for_collection,
    resolve_access_token,
    resolve_oauth_client,
    resolve_token_url,
)
from app.integrations.categories.idp.forgerock.oauth import exchange_client_credentials, merge_token_into_config
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import ForgeRockConfigureResponse, ForgeRockFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/forgerock", tags=["integrations", "idp", "forgerock"])
idp_router = APIRouter(prefix="/idp/forgerock", tags=["integrations", "idp", "forgerock"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("access_token", "client_secret", "forgerock_client_secret", "refresh_token"):
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
) -> ForgeRockConfigureResponse:
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
        return ForgeRockConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Set forgerock_token_url, forgerock_api_base, and OAuth client_id/client_secret.",
            configuration_data=masked,
        )

    if has_oauth_client(cfg) and not cfg.get("skip_token_exchange"):
        try:
            cid, csec = resolve_oauth_client(cfg)
            turl = resolve_token_url(cfg)
            scope = cfg.get("forgerock_oauth_scope")
            sc = str(scope).strip() if scope else None
            token_payload = exchange_client_credentials(
                token_url=turl,
                client_id=cid,
                client_secret=csec,
                scope=sc or None,
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

    if not validate_forgerock_credentials(cfg):
        return ForgeRockConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="User list request failed; check forgerock_users_path and token scopes.",
            configuration_data=masked,
        )

    background_tasks.add_task(
        run_forgerock_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return ForgeRockConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=True,
        ready_for_collection=True,
        collection_started_in_background=True,
        next_step="ForgeRock credentials valid. IAM evidence collection is running in the background.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=ForgeRockConfigureResponse)
def configure_forgerock(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> ForgeRockConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@idp_router.post("/integrations", response_model=ForgeRockConfigureResponse)
def configure_forgerock_idp(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> ForgeRockConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@router.get("/flow", response_model=ForgeRockFlowResponse)
def forgerock_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ForgeRockFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_collection(cfg):
        return ForgeRockFlowResponse(
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            next_step="Configure forgerock_token_url, forgerock_api_base, and OAuth client.",
        )
    token = resolve_access_token(cfg)
    ok = bool(token) and validate_forgerock_credentials(cfg)
    return ForgeRockFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Ready." if ok else "Token present but API validation failed.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def forgerock_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _tool_integration_response(row, configuration_data=_mask_configuration_data(cfg))
