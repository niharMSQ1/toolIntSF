"""Microsoft Defender for Cloud: Azure AD app + subscription (ARM Microsoft.Security)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.cspm.defender_cloud.api_client import DefenderCloudApiError, validate_connection
from app.integrations.categories.cspm.defender_cloud.collection_runner import (
    run_defender_cloud_evidence_collection_after_configure_background,
)
from app.integrations.categories.cspm.defender_cloud.credentials import (
    credentials_valid_shape,
    ready_for_collection,
    resolve_client_id,
    resolve_client_secret,
    resolve_subscription_id,
    resolve_tenant_id,
)
from app.integrations.categories.cspm.defender_cloud.token_refresh import ensure_arm_access_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    DefenderCloudConfigureResponse,
    DefenderCloudFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/cspm/defender-cloud", tags=["integrations", "cspm", "defender-cloud"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("client_secret", "azure_client_secret", "azure_access_token"):
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
    if str(data.get("provider_key", "")).strip().lower() == "defender_cloud":
        data["provider_key"] = "defender_cloud"
    return data


@router.post("/configure", response_model=DefenderCloudConfigureResponse)
def configure_defender_cloud(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> DefenderCloudConfigureResponse:
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
            validate_connection(
                resolve_tenant_id(cfg) or "",
                resolve_client_id(cfg) or "",
                resolve_client_secret(cfg) or "",
                resolve_subscription_id(cfg) or "",
            )
            cred_ok = True
        except DefenderCloudApiError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    row_after = persistence.get_integration(session, payload.org_id, payload.tool_id)
    if not row_after:
        raise HTTPException(status_code=500, detail="Integration row missing after upsert.")
    if cred_ok:
        cfg = ensure_arm_access_token(session, row_after)

    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg if isinstance(cfg, dict) else {})
    rdy = ready_for_collection(cfg) and cred_ok

    if rdy:
        background_tasks.add_task(
            run_defender_cloud_evidence_collection_after_configure_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )

    return DefenderCloudConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=rdy,
        collection_started_in_background=rdy,
        next_step=(
            "Integration ready. Defender for Cloud evidence collection started in the background."
            if rdy
            else "Set tenant_id, client_id, client_secret, subscription_id, then POST /configure again."
        ),
        configuration_data=masked,
    )


@router.get("/flow", response_model=DefenderCloudFlowResponse)
def defender_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> DefenderCloudFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    cred_ok = credentials_valid_shape(cfg)
    ok = ready_for_collection(cfg) and cred_ok
    return DefenderCloudFlowResponse(
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
