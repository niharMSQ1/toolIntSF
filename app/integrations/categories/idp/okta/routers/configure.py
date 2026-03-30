"""Okta IAM: configure, flow, status (org URL + SSWS API token)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.okta.collection_runner import (
    run_okta_evidence_collection_after_configure_background,
    validate_okta_credentials,
)
from app.integrations.categories.idp.okta.credentials import ready_for_collection, resolve_okta_base_url
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import OktaConfigureResponse, OktaFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/okta", tags=["integrations", "idp", "okta"])
idp_router = APIRouter(prefix="/idp/okta", tags=["integrations", "idp", "okta"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    if "api_token" in masked and masked["api_token"]:
        masked["api_token"] = "***"
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


def _configure_okta_response(
    payload: ToolIntegrationPayload,
    session: Session,
    background_tasks: BackgroundTasks,
) -> OktaConfigureResponse:
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
        return OktaConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step="Set org_domain and api_token in configuration_data, then POST /configure again.",
            configuration_data=masked,
        )

    try:
        resolve_okta_base_url(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not validate_okta_credentials(cfg):
        return OktaConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            credentials_valid=False,
            ready_for_collection=False,
            collection_started_in_background=False,
            next_step=(
                "Could not read Okta org with this API token (GET /api/v1/org). "
                "Check org_domain (use admin URL or tenant.okta.com; -admin is normalized) and token scopes."
            ),
            configuration_data=masked,
        )

    background_tasks.add_task(
        run_okta_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return OktaConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=True,
        ready_for_collection=True,
        collection_started_in_background=True,
        next_step=(
            "Okta credentials valid. Evidence collection is running in the background; "
            "no separate POST to /api/v1/evidence/okta/collect is required."
        ),
        configuration_data=masked,
    )


@router.post("/configure", response_model=OktaConfigureResponse)
def configure_okta(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> OktaConfigureResponse:
    return _configure_okta_response(payload, session, background_tasks)


@idp_router.post("/integrations", response_model=OktaConfigureResponse)
def configure_okta_idp_alias(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> OktaConfigureResponse:
    return _configure_okta_response(payload, session, background_tasks)


@router.get("/flow", response_model=OktaFlowResponse)
def okta_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> OktaFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    try:
        resolve_okta_base_url(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    rdy = ready_for_collection(cfg) and validate_okta_credentials(cfg)
    return OktaFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=rdy,
        ready_for_collection=rdy,
        next_step=(
            "Ready for collection."
            if rdy
            else "Set org_domain and api_token in configuration_data and POST /configure."
        ),
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
