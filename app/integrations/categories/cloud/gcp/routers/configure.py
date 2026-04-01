"""GCP: configure, flow, status."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.cloud.gcp.collection_runner import run_gcp_evidence_collection_after_configure_background
from app.integrations.categories.cloud.gcp.credentials import credentials_valid_shape, ready_for_collection
from app.integrations.categories.cloud.gcp.session import GcpAuthError, validate_gcp_access
from app.integrations.core.persistence import tool_integration_service as persistence
from app.models import Tools
from app.schemas import GcpConfigureResponse, GcpFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/cloud/gcp", tags=["integrations", "cloud", "gcp"])


def _assert_gcp_tool(session: Session, tool_id: str) -> None:
    try:
        tid = UUID(str(tool_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid tool_id.") from e
    tool = session.get(Tools, tid)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found.")
    name = str(getattr(tool, "name", "") or "").strip().lower()
    if "gcp" not in name and "google cloud" not in name and "google cloud platform" not in name:
        raise HTTPException(
            status_code=400,
            detail=f"tool_id does not belong to GCP (found tool name: {getattr(tool, 'name', None)!r}).",
        )


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("service_account_json", "gcp_service_account_json"):
        if masked.get(k):
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


@router.post("/configure", response_model=GcpConfigureResponse)
def configure_gcp(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> GcpConfigureResponse:
    _assert_gcp_tool(session, payload.tool_id)
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

    cfg = dict(row.get("configuration_data") or {})
    cred_ok = False
    if credentials_valid_shape(cfg):
        try:
            validate_gcp_access(cfg)
            cred_ok = True
        except GcpAuthError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"GCP validation failed: {e}") from e

    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg)
    rdy = ready_for_collection(cfg) and cred_ok
    if rdy:
        background_tasks.add_task(
            run_gcp_evidence_collection_after_configure_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )

    return GcpConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=rdy,
        collection_started_in_background=rdy,
        next_step=(
            "Integration ready. GCP evidence collection has been started in the background."
            if rdy
            else "Set project_id and service_account_json in configuration_data, then POST /configure again."
        ),
        configuration_data=masked,
    )


@router.get("/flow", response_model=GcpFlowResponse)
def gcp_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> GcpFlowResponse:
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
    return GcpFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=ok,
        next_step=(
            "Ready for collection."
            if ok
            else "Set project_id and service_account_json in configuration_data and POST /configure."
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
    return _tool_integration_response(row, configuration_data=_mask_configuration_data(cfg))

