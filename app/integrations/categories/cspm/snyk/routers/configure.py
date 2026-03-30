"""Snyk: configure, flow, status — API key, access token, or OAuth 2.0 client credentials + org/group scope."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.cspm.snyk.api_client import SnykApiError, validate_snyk_connection
from app.integrations.categories.cspm.snyk.collection_runner import run_snyk_evidence_collection_after_configure_background
from app.integrations.categories.cspm.snyk.credentials import (
    AUTH_TYPE_OAUTH2,
    has_credentials_for_api,
    oauth_client_credentials_present,
    ready_for_collection,
    resolve_auth_type,
    resolve_oauth_client_id,
    resolve_oauth_client_secret,
)
from app.integrations.categories.cspm.snyk.oauth import SnykOAuthError, exchange_client_credentials, merge_oauth_token_into_config
from app.integrations.categories.cspm.snyk.regions import resolve_rest_base_url
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    SnykConfigureResponse,
    SnykFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/cspm/snyk", tags=["integrations", "cspm", "snyk"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("snyk_api_token", "api_token", "token", "oauth_client_secret", "client_secret", "oauth_access_token"):
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


def _maybe_exchange_oauth(session: Session, row: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    """If OAuth2 client credentials are configured, exchange and persist access token."""
    if resolve_auth_type(cfg) != AUTH_TYPE_OAUTH2 or not oauth_client_credentials_present(cfg):
        return cfg
    region = cfg.get("region") if isinstance(cfg.get("region"), str) else None
    try:
        payload = exchange_client_credentials(
            resolve_oauth_client_id(cfg) or "",
            resolve_oauth_client_secret(cfg) or "",
            region,
        )
    except SnykOAuthError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    new_cfg = merge_oauth_token_into_config(cfg, payload)
    persistence.save_tool_integration_config(session, row["id"], new_cfg)
    return new_cfg


@router.post("/configure", response_model=SnykConfigureResponse)
def configure_snyk(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> SnykConfigureResponse:
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
    cfg = _maybe_exchange_oauth(session, row, cfg)

    cred_ok = has_credentials_for_api(cfg)
    if cred_ok:
        try:
            validate_snyk_connection(cfg)
        except SnykApiError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Snyk validation failed: {e}") from e

    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(cfg if isinstance(cfg, dict) else {})
    rdy = ready_for_collection(cfg) and cred_ok

    if rdy:
        background_tasks.add_task(
            run_snyk_evidence_collection_after_configure_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )

    return SnykConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=rdy,
        collection_started_in_background=rdy,
        next_step=(
            "Integration ready. Full Snyk evidence collection has been started in the background."
            if rdy
            else "Set credentials (api_key, access_token, or OAuth client_id/client_secret) and org_ids or group_id, then POST /configure again."
        ),
        configuration_data=masked,
    )


@router.get("/flow", response_model=SnykFlowResponse)
def snyk_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> SnykFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    cred_ok = has_credentials_for_api(cfg)
    ok = ready_for_collection(cfg) and cred_ok
    return SnykFlowResponse(
        organization_id=oid,
        tool_id=tid,
        credentials_valid=cred_ok,
        ready_for_collection=ok,
        next_step=(
            "Ready for collection."
            if ok
            else "Set auth_type (optional), token or OAuth credentials, region, and org_ids or group_id, then POST /configure."
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


@router.get("/regions")
def snyk_regions() -> dict[str, Any]:
    """Document default REST base for each supported region key."""
    return {
        "regions": [
            {"key": "us", "rest_base": resolve_rest_base_url("us")},
            {"key": "eu", "rest_base": resolve_rest_base_url("eu")},
            {"key": "au", "rest_base": resolve_rest_base_url("au")},
        ]
    }
