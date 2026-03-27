"""AWS cloud infrastructure configure endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.cloud_infra.aws.collection_runner import (
    run_aws_evidence_collection_after_configure_background,
)
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import AwsConfigureResponse, ToolIntegrationPayload

router = APIRouter(prefix="/api/v1/integrations/aws", tags=["integrations", "cloud_infra", "aws"])
cloud_router = APIRouter(prefix="/cloud/aws", tags=["integrations", "cloud_infra", "aws"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for key in ("secret_access_key",):
        if key in masked and masked[key]:
            masked[key] = "***"
    return masked


def _assert_configure_payload(session: Session, tool_id: str) -> None:
    tool = persistence.get_tool_catalog_entry(session, tool_id)
    tool_name = str(tool.get("name") or "").strip().lower()
    domain_name = str(tool.get("domain_name") or "").strip().lower()
    if tool_name != "aws":
        raise ValueError(f"Tool {tool_id!r} is not the AWS tool.")
    if not tool.get("domain_id"):
        raise ValueError("AWS tool has no domain_id; assign the CLOUD_INFRA domain in tools first.")
    if domain_name != "cloud_infra":
        raise ValueError(
            f"AWS tool must belong to CLOUD_INFRA, but tools.domain_id resolves to {tool.get('domain_name')!r}."
        )


def _configure_impl(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session,
) -> AwsConfigureResponse:
    try:
        _assert_configure_payload(session, payload.tool_id)
        row = persistence.upsert_tool_integration(
            session,
            org_id=payload.org_id,
            tool_id=payload.tool_id,
            user_id=payload.user_id,
            configuration_data=dict(payload.configuration_data),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    background_tasks.add_task(
        run_aws_evidence_collection_after_configure_background,
        payload.org_id,
        payload.tool_id,
        payload.user_id,
    )
    return AwsConfigureResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        configured=True,
        collection_started=True,
        next_step=(
            "Integration saved and AWS evidence collection started in the background. "
            "Use POST /api/v1/evidence/aws/collect or POST /api/v1/integrations/sync to re-run."
        ),
        configuration_data=_mask_configuration_data(row["configuration_data"]),
    )


@router.post("/configure", response_model=AwsConfigureResponse)
def configure_aws(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> AwsConfigureResponse:
    return _configure_impl(payload, background_tasks, session)


@cloud_router.post("/integrations", response_model=AwsConfigureResponse)
def configure_aws_alias(
    payload: ToolIntegrationPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> AwsConfigureResponse:
    return _configure_impl(payload, background_tasks, session)
