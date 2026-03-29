"""Prisma Cloud CSPM: configure, flow, status (access key + API URL)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.cspm.prisma_cloud.api_client import PrismaCloudApiError, validate_connection
from app.integrations.categories.cspm.prisma_cloud.collection_runner import (
    run_prisma_cloud_evidence_collection_after_configure_background,
)
from app.integrations.categories.cspm.prisma_cloud.credentials import (
    credentials_valid_shape,
    ready_for_collection,
    resolve_access_key_id,
    resolve_api_base_url,
    resolve_secret_key,
)
from app.integrations.categories.cspm.prisma_cloud.token_refresh import ensure_prisma_jwt
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    PrismaCloudConfigureResponse,
    PrismaCloudFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/cspm/prisma-cloud", tags=["integrations", "cspm", "prisma-cloud"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("secret_key", "password", "prisma_jwt"):
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
    pk = str(data.get("provider_key", "")).strip().lower()
    if pk == "prisma_cloud":
        data["provider_key"] = "prisma_cloud"
    return data


@router.post("/configure", response_model=PrismaCloudConfigureResponse)
def configure_prisma_cloud(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> PrismaCloudConfigureResponse:
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
                resolve_api_base_url(cfg),
                resolve_access_key_id(cfg) or "",
                resolve_secret_key(cfg) or "",
            )
            cred_ok = True
        except PrismaCloudApiError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    elif resolve_api_base_url(cfg) and (resolve_access_key_id(cfg) or resolve_secret_key(cfg)):
        raise HTTPException(
            status_code=400,
            detail="api_base_url must be https://… and access_key_id + secret_key are required.",
        )

    row_after = persistence.get_integration(session, payload.org_id, payload.tool_id)
    if not row_after:
        raise HTTPException(status_code=500, detail="Integration row missing after upsert.")
    if cred_ok:
        cfg = ensure_prisma_jwt(session, row_after)

    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg if isinstance(cfg, dict) else {})
    rdy = ready_for_collection(cfg) and cred_ok

    if rdy:
        background_tasks.add_task(
            run_prisma_cloud_evidence_collection_after_configure_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )

    return PrismaCloudConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=rdy,
        collection_started_in_background=rdy,
        next_step=(
            "Integration ready. Prisma Cloud evidence collection started in the background."
            if rdy
            else "Set api_base_url, access_key_id, and secret_key, then POST /configure again."
        ),
        configuration_data=masked,
    )


@router.get("/flow", response_model=PrismaCloudFlowResponse)
def prisma_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> PrismaCloudFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    cred_ok = credentials_valid_shape(cfg)
    ok = ready_for_collection(cfg) and cred_ok
    return PrismaCloudFlowResponse(
        organization_id=oid,
        tool_id=tid,
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
    masked = _mask_configuration_data(cfg)
    return _tool_integration_response(row, configuration_data=masked)
