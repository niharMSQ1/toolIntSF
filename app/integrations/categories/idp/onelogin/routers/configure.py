"""OneLogin: configure, flow, status."""

from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.onelogin.collection_runner import (
    run_onelogin_evidence_collection_after_configure_background,
    validate_onelogin_credentials,
)
from app.integrations.categories.idp.onelogin.credentials import (
    has_access_token,
    has_oauth_client,
    ready_for_collection,
    resolve_access_token,
    resolve_oauth_client,
)
from app.integrations.categories.idp.onelogin.oauth import exchange_client_credentials, merge_token_into_config
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import OneLoginConfigureResponse, OneLoginFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/onelogin", tags=["integrations", "idp", "onelogin"])
idp_router = APIRouter(prefix="/idp/onelogin", tags=["integrations", "idp", "onelogin"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("access_token", "client_secret", "onelogin_client_secret", "refresh_token"):
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
) -> OneLoginConfigureResponse:
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
        return OneLoginConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Set client_id and client_secret (or access_token with skip_token_exchange).",
            configuration_data=masked,
        )

    if has_oauth_client(cfg) and not cfg.get("skip_token_exchange"):
        try:
            cid, csec = resolve_oauth_client(cfg)
            token_payload = exchange_client_credentials(cfg=cfg, client_id=cid, client_secret=csec)
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

    if not validate_onelogin_credentials(cfg):
        return OneLoginConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Users API request failed; check onelogin_region and API access.",
            configuration_data=masked,
        )

    background_tasks.add_task(
        run_onelogin_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return OneLoginConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=True,
        ready_for_collection=True,
        collection_started_in_background=True,
        next_step="OneLogin credentials valid. IAM evidence collection is running in the background.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=OneLoginConfigureResponse)
def configure_onelogin(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> OneLoginConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@idp_router.post("/integrations", response_model=OneLoginConfigureResponse)
def configure_onelogin_idp(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> OneLoginConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@router.get("/flow", response_model=OneLoginFlowResponse)
def onelogin_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> OneLoginFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_collection(cfg):
        return OneLoginFlowResponse(
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            next_step="Configure OneLogin OAuth client.",
        )
    token = resolve_access_token(cfg)
    ok = bool(token) and validate_onelogin_credentials(cfg)
    return OneLoginFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Ready." if ok else "Token present but API validation failed.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def onelogin_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _tool_integration_response(row, configuration_data=_mask_configuration_data(cfg))
