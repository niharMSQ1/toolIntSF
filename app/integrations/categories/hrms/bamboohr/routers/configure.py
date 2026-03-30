<<<<<<< HEAD
"""BambooHR: configure, flow, and status (HRMS category)."""

from __future__ import annotations

from typing import Any

=======
"""BambooHR: API key + subdomain."""

from __future__ import annotations

import logging

import httpx
>>>>>>> master
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
<<<<<<< HEAD
from app.integrations.categories.hrms.bamboohr.credentials import (
    AUTH_MODE_API_KEY,
    AUTH_MODE_APP_OAUTH,
    has_usable_credentials,
    resolve_auth_mode,
    resolve_client_credentials,
    resolve_redirect_uri,
    resolve_subdomain,
)
from app.integrations.categories.hrms.bamboohr.oauth import build_authorization_url, build_state
from app.integrations.categories.hrms.bamboohr.seed_service import seed_bamboohr_evidence_masters
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    BambooConfigureResponse,
    BambooFlowResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)

router = APIRouter(prefix="/api/v1/integrations/bamboohr", tags=["integrations", "hrms", "bamboohr"])
hrms_router = APIRouter(prefix="/hrms/bamboohr", tags=["integrations", "hrms", "bamboohr"])


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    """Mask BambooHR secrets before returning saved configuration to callers."""
    masked = dict(cfg)
    for key in ("api_key", "access_token", "refresh_token", "client_secret"):
        if key in masked and masked[key]:
            masked[key] = "***"
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


def _next_step_for_mode(
    cfg: dict[str, Any],
    *,
    org_id: str,
    tool_id: str,
) -> tuple[bool, str, str | None, str | None]:
    """Describe the next action based on BambooHR auth mode and saved credentials."""
    mode = resolve_auth_mode(cfg)

    if mode == AUTH_MODE_API_KEY:
        if has_usable_credentials(cfg):
            return True, (
                "BambooHR API key credentials are saved and the integration is ready for API calls. "
                "You can now use employee preview routes or POST /api/v1/evidence/bamboohr/collect."
            ), None, None
        return False, (
            "Provide both BambooHR subdomain and api_key in configuration_data to use API key authentication."
        ), None, None

    if mode == AUTH_MODE_APP_OAUTH and has_usable_credentials(cfg):
        return True, (
            "BambooHR app auth credentials are already saved and the integration is ready for API calls. "
            "You can now use employee preview routes or POST /api/v1/evidence/bamboohr/collect."
        ), None, None

    client_id, _secret = resolve_client_credentials(cfg)
    redirect_uri = resolve_redirect_uri(cfg)
    company_domain = resolve_subdomain(cfg)
    state = build_state(org_id, tool_id)
    auth_url = build_authorization_url(
        company_domain=company_domain,
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
    )

    return False, (
        "BambooHR app auth is selected, but the browser OAuth/connect route is the next step to implement. "
        "Use authorization_url or the /connect route to complete BambooHR app auth."
    ), auth_url, state


def _configure_bamboohr_response(
    payload: ToolIntegrationPayload,
    session: Session,
) -> BambooConfigureResponse:
=======
from app.integrations.categories.hrms._shared_routes import mask_configuration_data, tool_integration_response
from app.integrations.categories.hrms.bamboohr import api_client
from app.integrations.categories.hrms.bamboohr.credentials import ready_for_api_calls, resolve_api_key, resolve_subdomain
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import BambooHrConfigureResponse, BambooHrFlowResponse, ToolIntegrationPayload, ToolIntegrationResponse

logger = logging.getLogger("app.integrations.bamboohr")

router = APIRouter(prefix="/api/v1/integrations/hrms/bamboohr", tags=["integrations", "hrms", "bamboohr"])

_SECRET_KEYS = ("bamboohr_api_key", "api_key", "webhook_secret")


@router.post("/configure", response_model=BambooHrConfigureResponse)
def configure(payload: ToolIntegrationPayload, session: Session = Depends(get_db)) -> BambooHrConfigureResponse:
>>>>>>> master
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
<<<<<<< HEAD

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")

    seed_bamboohr_evidence_masters(session, payload.tool_id)

    try:
        oauth_complete, next_step, authorization_url, state = _next_step_for_mode(
            cfg,
            org_id=payload.org_id,
            tool_id=payload.tool_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    masked = _mask_configuration_data(cfg)
    return BambooConfigureResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        oauth_complete=oauth_complete,
        authorization_url=authorization_url,
        state=state,
        next_step=next_step,
=======
    cfg = dict(row["configuration_data"])
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")

    oid = str(row["organization_id"])
    tid = str(row["tool_id"])

    try:
        resolve_subdomain(cfg)
        key = resolve_api_key(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    ok = False
    try:
        ok = api_client.validate_connection(cfg, key)
    except httpx.HTTPStatusError as e:
        logger.warning("BambooHR validation HTTP error: %s", e.response.status_code)
        raise HTTPException(status_code=400, detail=e.response.text[:2000]) from e

    masked = mask_configuration_data(cfg, _SECRET_KEYS)

    return BambooHrConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        credentials_valid=ok,
        ready_for_collection=ok,
        next_step="GET .../hrms/bamboohr/employees when credentials_valid is true.",
>>>>>>> master
        configuration_data=masked,
    )


<<<<<<< HEAD
@router.post("/configure", response_model=BambooConfigureResponse)
def configure_bamboohr(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
) -> BambooConfigureResponse:
    return _configure_bamboohr_response(payload, session)


@hrms_router.post("/integrations", response_model=BambooConfigureResponse)
def configure_bamboohr_hrms_alias(
    payload: ToolIntegrationPayload,
    session: Session = Depends(get_db),
) -> BambooConfigureResponse:
    return _configure_bamboohr_response(payload, session)


@router.get("/flow", response_model=BambooFlowResponse)
def bamboohr_flow_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> BambooFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")

    try:
        oauth_complete, next_step, authorization_url, state = _next_step_for_mode(
            cfg,
            org_id=org_id,
            tool_id=tool_id,
        )
        redirect_uri = resolve_redirect_uri(cfg) if resolve_auth_mode(cfg) == AUTH_MODE_APP_OAUTH else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return BambooFlowResponse(
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        oauth_complete=oauth_complete,
        redirect_uri=redirect_uri,
        next_step=next_step,
        authorization_url=authorization_url,
        state=state,
        collect_post_json_example=None,
=======
@router.get("/flow", response_model=BambooHrFlowResponse)
def flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> BambooHrFlowResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    if not ready_for_api_calls(cfg):
        return BambooHrFlowResponse(
            organization_id=oid,
            tool_id=tid,
            ready_for_collection=False,
            next_step="Configure bamboohr_subdomain and bamboohr_api_key.",
        )
    try:
        key = resolve_api_key(cfg)
        ok = api_client.validate_connection(cfg, key)
    except (ValueError, httpx.HTTPStatusError):
        ok = False
    return BambooHrFlowResponse(
        organization_id=oid,
        tool_id=tid,
        ready_for_collection=ok,
        next_step="Ready." if ok else "BambooHR directory call failed.",
>>>>>>> master
    )


@router.get("/status", response_model=ToolIntegrationResponse)
<<<<<<< HEAD
def bamboohr_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")

    return _tool_integration_response(row, configuration_data=_mask_configuration_data(cfg))
=======
def status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    return tool_integration_response(row, configuration_data=mask_configuration_data(cfg, _SECRET_KEYS))
>>>>>>> master
