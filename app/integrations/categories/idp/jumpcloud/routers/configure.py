"""JumpCloud: configure, flow, status."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.jumpcloud.collection_runner import (
    run_jumpcloud_evidence_collection_after_configure_background,
    validate_jumpcloud_credentials,
)
from app.integrations.categories.idp.jumpcloud.credentials import ready_for_collection
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import JumpCloudConfigureResponse, JumpCloudFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/jumpcloud", tags=["integrations", "idp", "jumpcloud"])
idp_router = APIRouter(prefix="/idp/jumpcloud", tags=["integrations", "idp", "jumpcloud"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("jumpcloud_api_key", "api_key"):
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
) -> JumpCloudConfigureResponse:
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
        return JumpCloudConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Set jumpcloud_api_key, then POST /configure again.",
            configuration_data=masked,
        )

    if not validate_jumpcloud_credentials(cfg):
        return JumpCloudConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="systemusers request failed; check API key scope.",
            configuration_data=masked,
        )

    background_tasks.add_task(
        run_jumpcloud_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return JumpCloudConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=True,
        ready_for_collection=True,
        collection_started_in_background=True,
        next_step="JumpCloud API key valid. IAM evidence collection is running in the background.",
        configuration_data=masked,
    )


@router.post("/configure", response_model=JumpCloudConfigureResponse)
def configure_jumpcloud(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> JumpCloudConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@idp_router.post("/integrations", response_model=JumpCloudConfigureResponse)
def configure_jumpcloud_idp(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> JumpCloudConfigureResponse:
    return _configure_response(payload, session, background_tasks)


@router.get("/flow", response_model=JumpCloudFlowResponse)
def jumpcloud_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> JumpCloudFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_collection(cfg):
        return JumpCloudFlowResponse(
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            next_step="Configure jumpcloud_api_key.",
        )
    ok = validate_jumpcloud_credentials(cfg)
    return JumpCloudFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="Ready." if ok else "API key present but validation failed.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def jumpcloud_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _tool_integration_response(row, configuration_data=_mask_configuration_data(cfg))
