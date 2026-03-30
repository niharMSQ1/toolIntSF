"""CyberArk Identity: configure, flow, status."""

from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.cyberark.collection_runner import (
    run_cyberark_evidence_collection_after_configure_background,
    validate_cyberark_credentials,
)
from app.integrations.categories.idp.cyberark.credentials import (
    has_access_token,
    has_oauth_client,
    ready_for_collection,
    resolve_access_token,
    resolve_identity_base_url,
    resolve_oauth_client,
    resolve_oauth_scope,
)
from app.integrations.categories.idp.cyberark.oauth import exchange_client_credentials, merge_token_into_config
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import CyberArkConfigureResponse, CyberArkFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/cyberark-identity", tags=["integrations", "idp", "cyberark"])
idp_router = APIRouter(prefix="/idp/cyberark-identity", tags=["integrations", "idp", "cyberark"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("access_token", "client_secret", "cyberark_client_secret", "refresh_token"):
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
) -> CyberArkConfigureResponse:
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
        return CyberArkConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Set cyberark_identity_base_url and OAuth client_id/client_secret, then POST /configure again.",
            configuration_data=masked,
        )

    if has_oauth_client(cfg) and not cfg.get("skip_token_exchange"):
        try:
            cid, csec = resolve_oauth_client(cfg)
            base = resolve_identity_base_url(cfg)
            scope = resolve_oauth_scope(cfg)
            token_payload = exchange_client_credentials(
                identity_base_url=base,
                client_id=cid,
                client_secret=csec,
                scope=scope,
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

    if not validate_cyberark_credentials(cfg):
        return CyberArkConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="SCIM Users request failed; check OAuth scopes and SCIM path (cyberark_scim_users_path).",
            configuration_data=masked,
        )

    background_tasks.add_task(
        run_cyberark_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return CyberArkConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=True,
        ready_for_collection=True,
        collection_started_in_background=True,
        next_step="CyberArk Identity credentials valid. IAM evidence collection is running in the background.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=CyberArkConfigureResponse)
def configure_cyberark(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> CyberArkConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@idp_router.post("/integrations", response_model=CyberArkConfigureResponse)
def configure_cyberark_idp(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> CyberArkConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@router.get("/flow", response_model=CyberArkFlowResponse)
def cyberark_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> CyberArkFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_collection(cfg):
        return CyberArkFlowResponse(
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            next_step="Configure cyberark_identity_base_url and OAuth client.",
        )
    token = resolve_access_token(cfg)
    ok = bool(token) and validate_cyberark_credentials(cfg)
    return CyberArkFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Ready." if ok else "Token present but SCIM validation failed.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def cyberark_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _tool_integration_response(row, configuration_data=_mask_configuration_data(cfg))
