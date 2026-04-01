from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.linear.collection_runner import (
    run_evidence_collection_after_config_background,
)
from app.integrations.categories.project_management.linear.credentials import has_api_key
from app.integrations.core.persistence import tool_integration_service as persistence
from app.models import Tools
from app.schemas import PmTokenConfigureResponse, PmTokenFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations/project-management/linear", tags=["integrations", "project-management", "linear"])
pm_router = APIRouter(prefix="/project-management/linear", tags=["integrations", "project-management", "linear"])


def _mask(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("api_key", "linear_api_key", "access_token"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def _assert_linear_tool(session: Session, tool_id: str) -> None:
    try:
        tid = UUID(str(tool_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid tool_id.") from e
    tool = session.get(Tools, tid)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found.")
    name = str(getattr(tool, "name", "") or "").strip().lower()
    if "linear" not in name:
        raise HTTPException(
            status_code=400,
            detail=f"tool_id does not belong to Linear (found tool name: {getattr(tool, 'name', None)!r}).",
        )


def _cfg(
    payload: ToolIntegrationPayload,
    session: Session,
    background_tasks: BackgroundTasks | None = None,
) -> PmTokenConfigureResponse:
    _assert_linear_tool(session, payload.tool_id)

    data = dict(payload.configuration_data)
    if any(k in data for k in ("bamboohr_subdomain", "bamboohr_api_key")):
        raise HTTPException(
            status_code=400,
            detail="Linear configure accepts api_key/linear_api_key only; BambooHR keys are not allowed.",
        )
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
    ok = has_api_key(cfg)
    if ok and background_tasks is not None:
        background_tasks.add_task(
            run_evidence_collection_after_config_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )
    return PmTokenConfigureResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        token_configured=ok,
        next_step=(
            "Linear configured. Evidence collection has been started in the background."
            if ok
            else "Set api_key (Linear personal API key)."
        ),
        configuration_data=_mask(cfg),
    )


@router.post("/configure", response_model=PmTokenConfigureResponse)
def configure(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> PmTokenConfigureResponse:
    return _cfg(payload, session, background_tasks)


@pm_router.post("/integrations", response_model=PmTokenConfigureResponse)
def configure_a(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> PmTokenConfigureResponse:
    return _cfg(payload, session, background_tasks)


@router.get("/flow", response_model=PmTokenFlowResponse)
def flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> PmTokenFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    ok = has_api_key(cfg)
    return PmTokenFlowResponse(
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        token_configured=ok,
        next_step="Ready." if ok else "Add api_key.",
    )


@router.get("/status", response_model=ToolIntegrationResponse)
def status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return ToolIntegrationResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        configuration_data=_mask(cfg),
    )
