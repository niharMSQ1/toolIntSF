"""AWS: configure, flow, status (IAM role ARN + optional external ID for STS AssumeRole)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.cloud.aws.collection_runner import run_aws_evidence_collection_after_configure_background
from app.integrations.categories.cloud.aws.credentials import (
    credentials_valid_shape,
    has_role_arn,
    ready_for_collection,
    resolve_role_arn,
)
from app.integrations.categories.cloud.aws.session import AwsAssumeRoleError, validate_assume_role
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    AwsConfigureResponse,
    AwsFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/cloud/aws", tags=["integrations", "cloud", "aws"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    if masked.get("external_id"):
        masked["external_id"] = "***"
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
    """Persist provider_key if present; require non-empty role_arn for a valid integration."""
    data = dict(raw)
    if "provider_key" in data and str(data.get("provider_key", "")).strip().lower() == "aws":
        data["provider_key"] = "aws"
    return data


@router.post("/configure", response_model=AwsConfigureResponse)
def configure_aws(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> AwsConfigureResponse:
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
    rarn = resolve_role_arn(cfg)
    if rarn and credentials_valid_shape(cfg):
        try:
            validate_assume_role(cfg)
            cred_ok = True
        except AwsAssumeRoleError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            ) from e
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"AWS validation failed: {e}") from e
    elif rarn and not credentials_valid_shape(cfg):
        raise HTTPException(
            status_code=400,
            detail="role_arn must look like arn:aws:iam::<account-id>:role/<role-name>",
        )

    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg if isinstance(cfg, dict) else {})
    rdy = ready_for_collection(cfg) and cred_ok

    if rdy:
        background_tasks.add_task(
            run_aws_evidence_collection_after_configure_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )

    return AwsConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=rdy,
        collection_started_in_background=rdy,
        next_step=(
            "Integration ready. AWS evidence collection has been started in the background."
            if rdy
            else "Set configuration_data.role_arn to a valid IAM role ARN your server can assume, then POST /configure again."
        ),
        configuration_data=masked,
    )


@router.get("/flow", response_model=AwsFlowResponse)
def aws_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> AwsFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    cred_ok = has_role_arn(cfg) and credentials_valid_shape(cfg)
    ok = ready_for_collection(cfg) and cred_ok
    return AwsFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=ok,
        next_step=(
            "Ready for collection."
            if ok
            else "Set role_arn (and optional external_id, region) in configuration_data and POST /configure."
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
