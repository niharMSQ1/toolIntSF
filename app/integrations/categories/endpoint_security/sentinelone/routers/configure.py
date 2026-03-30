"""SentinelOne: API token + console URL."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.endpoint_security.sentinelone.api_client import SentinelOneApiError, validate_credentials
from app.integrations.categories.endpoint_security.sentinelone.collection_runner import (
    run_sentinelone_evidence_collection_after_configure_background,
)
from app.integrations.categories.endpoint_security.sentinelone.credentials import (
    credentials_valid_shape,
    ready_for_collection,
    resolve_api_base_url,
    resolve_api_token,
    resolve_verify_tls,
)
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    SentinelOneConfigureResponse,
    SentinelOneFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(
    prefix="/api/v1/integrations/endpoint/sentinelone",
    tags=["integrations", "endpoint", "sentinelone"],
)


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("api_token", "sentinelone_api_token"):
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


def _normalize_configuration_data(raw: dict[str, Any]) -> dict[str, Any]:
    data = dict(raw)
    if str(data.get("provider_key", "")).strip().lower() == "sentinelone":
        data["provider_key"] = "sentinelone"
    return data


@router.post("/configure", response_model=SentinelOneConfigureResponse)
def configure_sentinelone(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> SentinelOneConfigureResponse:
    data = _normalize_configuration_data(dict(payload.configuration_data))
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

    cfg = dict(row.get("configuration_data") or {})
    cred_ok = False
    if credentials_valid_shape(cfg):
        try:
            validate_credentials(
                resolve_api_base_url(cfg),
                resolve_api_token(cfg) or "",
                verify_tls=resolve_verify_tls(cfg),
            )
            cred_ok = True
        except SentinelOneApiError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg)
    rdy = ready_for_collection(cfg) and cred_ok

    if rdy:
        background_tasks.add_task(
            run_sentinelone_evidence_collection_after_configure_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )

    return SentinelOneConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=rdy,
        collection_started_in_background=rdy,
        next_step=(
            "Integration ready. SentinelOne evidence collection started in the background."
            if rdy
            else "Set api_token and api_base_url (management console origin or full .../web/api/v2.1 URL), then POST /configure again."
        ),
        configuration_data=masked,
    )


@router.get("/flow", response_model=SentinelOneFlowResponse)
def sentinelone_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> SentinelOneFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    cred_ok = credentials_valid_shape(cfg)
    ok = ready_for_collection(cfg) and cred_ok
    return SentinelOneFlowResponse(
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        credentials_valid=cred_ok,
        ready_for_collection=ok,
        next_step="Ready for collection." if ok else "Complete configuration in POST /configure.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def integration_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return _tool_integration_response(row, configuration_data=_mask_configuration_data(cfg))
