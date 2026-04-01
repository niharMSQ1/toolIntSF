"""Microsoft Entra: configure, flow, status, token refresh — commercial and GCC High."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import get_tool_integration_payload
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.integrations.categories.idp.microsoft_entra.collection_runner import (
    run_entra_evidence_collection_after_oauth_background,
)
from app.integrations.categories.idp.microsoft_entra.credentials import (
    default_redirect_from_settings,
    has_access_token,
    resolve_oauth_application_credentials,
    resolve_redirect_uri,
    resolve_scopes,
    resolve_tenant_id,
)
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud
from app.integrations.categories.idp.microsoft_entra.oauth import build_authorization_url, build_state
from app.integrations.categories.idp.microsoft_entra.token_refresh import refresh_entra_access_tokens
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import (
    EntraConfigureResponse,
    EntraFlowResponse,
    EntraRefreshTokensBody,
    EntraRefreshTokensResponse,
    ToolIntegrationPayload,
    ToolIntegrationResponse,
)


def _mask_configuration_data(cfg: dict[str, Any]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in ("access_token", "refresh_token", "client_secret"):
        if k in masked and masked[k]:
            masked[k] = "***"
    oc = masked.get("oauth_clients")
    if isinstance(oc, list):
        masked["oauth_clients"] = []
        for x in oc:
            if not isinstance(x, dict):
                masked["oauth_clients"].append(x)
                continue
            m = dict(x)
            for kk in ("access_token", "refresh_token", "client_secret"):
                if kk in m and m[kk]:
                    m[kk] = "***"
            masked["oauth_clients"].append(m)
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


def _normalize_entra_payload(
    payload: ToolIntegrationPayload,
    *,
    cloud: NationalCloud,
    settings: Settings,
) -> dict[str, Any]:
    """Pin national_cloud, tenant, redirect_uri, and oauth_clients shell (Vanta-style: secrets from env)."""
    data = dict(payload.configuration_data)
    data["national_cloud"] = cloud.value
    tid = str(data.get("tenant_id") or "common")
    data["tenant_id"] = tid

    redir = data.get("redirect_uri")
    if not redir or not str(redir).strip():
        redir = default_redirect_from_settings(settings, cloud)
    if not redir or not str(redir).strip():
        raise ValueError(
            "Missing redirect_uri: set ENTRA_REDIRECT_URI / ENTRA_GCC_HIGH_REDIRECT_URI or pass redirect_uri."
        )
    data["redirect_uri"] = str(redir).strip()

    if not data.get("oauth_clients"):
        entry: dict[str, Any] = {
            "tenant_id": tid,
            "national_cloud": cloud.value,
            "redirect_uri": data["redirect_uri"],
        }
        if data.get("client_id"):
            entry["client_id"] = str(data["client_id"])
        if data.get("client_secret") is not None:
            entry["client_secret"] = str(data["client_secret"])
        if data.get("scopes"):
            entry["scopes"] = str(data["scopes"])
        data["oauth_clients"] = [entry]

    # Validate app credentials exist (env or BYO)
    resolve_oauth_application_credentials(data, settings=settings, cloud=cloud)
    resolve_redirect_uri(data, settings=settings, cloud=cloud)
    return data


def _configure_entra_response(
    payload: ToolIntegrationPayload,
    session: Session,
    background_tasks: BackgroundTasks,
    *,
    cloud: NationalCloud,
    settings: Settings,
) -> EntraConfigureResponse:
    try:
        data = _normalize_entra_payload(payload, cloud=cloud, settings=settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

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

    if has_access_token(cfg):
        background_tasks.add_task(
            run_entra_evidence_collection_after_oauth_background,
            payload.org_id,
            payload.tool_id,
            payload.user_id,
        )
        return EntraConfigureResponse(
            id=str(row["id"]),
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            authorization_url=None,
            state=None,
            next_step=(
                "OAuth tokens already on this integration. Evidence collection has been started in the background."
            ),
            configuration_data=masked,
        )

    try:
        client_id, _secret = resolve_oauth_application_credentials(cfg, settings=settings, cloud=cloud)
        redir = resolve_redirect_uri(cfg, settings=settings, cloud=cloud)
        tenant = resolve_tenant_id(cfg)
        scopes = resolve_scopes(cfg, cloud=cloud)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(payload.org_id, payload.tool_id)
    auth_url = build_authorization_url(
        client_id=client_id,
        redirect_uri=redir,
        tenant_id=tenant,
        state=state,
        cloud=cloud,
        scopes=scopes,
    )
    return EntraConfigureResponse(
        id=str(row["id"]),
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        authorization_url=auth_url,
        state=state,
        next_step=(
            "Open authorization_url in a browser. Admin consent may be required for Microsoft Graph. "
            "After redirect, evidence collection runs in the background."
        ),
        configuration_data=masked,
    )


def _entra_refresh_impl(
    payload: EntraRefreshTokensBody,
    session: Session,
    *,
    cloud: NationalCloud,
) -> EntraRefreshTokensResponse:
    row = persistence.get_integration(session, payload.org_id, payload.tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row.get("configuration_data")
    if isinstance(cfg, dict) and cloud.value != cfg.get("national_cloud"):
        raise HTTPException(
            status_code=400,
            detail="This integration does not match this route; use the matching entra vs entra-gcc-high URLs.",
        )
    try:
        new_cfg, did_refresh = refresh_entra_access_tokens(session, row, force=payload.force)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    masked = _mask_configuration_data(new_cfg)
    msg = (
        "Access token refreshed from Microsoft."
        if did_refresh
        else "Access token still valid; token endpoint was not called. Use force=true to refresh anyway."
    )
    return EntraRefreshTokensResponse(
        ok=True,
        organization_id=oid,
        tool_id=tid,
        refreshed=did_refresh,
        message=msg,
        configuration_data=masked,
    )


def _entra_flow_impl(
    org_id: str,
    tool_id: str,
    session: Session,
    *,
    cloud: NationalCloud,
) -> EntraFlowResponse:
    settings = get_settings()
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    if cloud.value != cfg.get("national_cloud"):
        raise HTTPException(
            status_code=400,
            detail="Use the flow endpoint that matches this integration's cloud (entra vs entra-gcc-high).",
        )
    oid = str(row["organization_id"])
    tid = str(row["tool_id"])
    try:
        redirect = resolve_redirect_uri(cfg, settings=settings, cloud=cloud)
    except ValueError:
        redirect = cfg.get("redirect_uri")
    has_token = has_access_token(cfg)

    if has_token:
        return EntraFlowResponse(
            organization_id=oid,
            tool_id=tid,
            oauth_complete=True,
            redirect_uri=redirect,
            next_step="OAuth is complete. Evidence collection runs after redirect or is already in progress.",
            collect_post_json_example=None,
        )

    try:
        client_id, _secret = resolve_oauth_application_credentials(cfg, settings=settings, cloud=cloud)
        redir = resolve_redirect_uri(cfg, settings=settings, cloud=cloud)
        tenant = resolve_tenant_id(cfg)
        scopes = resolve_scopes(cfg, cloud=cloud)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(org_id, tool_id)
    auth_url = build_authorization_url(
        client_id=client_id,
        redirect_uri=redir,
        tenant_id=tenant,
        state=state,
        cloud=cloud,
        scopes=scopes,
    )
    return EntraFlowResponse(
        organization_id=oid,
        tool_id=tid,
        oauth_complete=False,
        redirect_uri=redirect,
        next_step="Open authorization_url. Ensure redirect_uri matches your Entra app registration.",
        authorization_url=auth_url,
        state=state,
        collect_post_json_example=None,
    )


def _entra_status_impl(
    org_id: str,
    tool_id: str,
    session: Session,
    *,
    cloud: NationalCloud,
) -> ToolIntegrationResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    if cloud.value != cfg.get("national_cloud"):
        raise HTTPException(status_code=400, detail="Use the status URL for this integration's cloud.")
    masked = _mask_configuration_data(cfg)
    return _tool_integration_response(row, configuration_data=masked)


# --- Commercial (worldwide) ---
commercial_router = APIRouter(
    prefix="/api/v1/integrations/entra",
    tags=["integrations", "idp", "microsoft_entra"],
)
commercial_idp_router = APIRouter(prefix="/idp/entra", tags=["integrations", "idp", "microsoft_entra"])


@commercial_router.post("/configure", response_model=EntraConfigureResponse)
def configure_entra_commercial(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> EntraConfigureResponse:
    return _configure_entra_response(
        payload, session, background_tasks, cloud=NationalCloud.COMMERCIAL, settings=settings
    )


@commercial_idp_router.post("/integrations", response_model=EntraConfigureResponse)
def configure_entra_commercial_alias(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> EntraConfigureResponse:
    return _configure_entra_response(
        payload, session, background_tasks, cloud=NationalCloud.COMMERCIAL, settings=settings
    )


# --- GCC High ---
gcc_high_router = APIRouter(
    prefix="/api/v1/integrations/entra-gcc-high",
    tags=["integrations", "idp", "microsoft_entra_gcc_high"],
)
gcc_high_idp_router = APIRouter(
    prefix="/idp/entra-gcc-high",
    tags=["integrations", "idp", "microsoft_entra_gcc_high"],
)


@gcc_high_router.post("/configure", response_model=EntraConfigureResponse)
def configure_entra_gcc_high(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> EntraConfigureResponse:
    return _configure_entra_response(
        payload, session, background_tasks, cloud=NationalCloud.GCC_HIGH, settings=settings
    )


@gcc_high_idp_router.post("/integrations", response_model=EntraConfigureResponse)
def configure_entra_gcc_high_alias(
    payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> EntraConfigureResponse:
    return _configure_entra_response(
        payload, session, background_tasks, cloud=NationalCloud.GCC_HIGH, settings=settings
    )


@commercial_router.post("/refresh-tokens", response_model=EntraRefreshTokensResponse)
def commercial_entra_refresh_tokens(
    payload: EntraRefreshTokensBody, session: Session = Depends(get_db)
) -> EntraRefreshTokensResponse:
    return _entra_refresh_impl(payload, session, cloud=NationalCloud.COMMERCIAL)


@commercial_router.get("/flow", response_model=EntraFlowResponse)
def commercial_entra_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> EntraFlowResponse:
    return _entra_flow_impl(org_id, tool_id, session, cloud=NationalCloud.COMMERCIAL)


@commercial_router.get("/status", response_model=ToolIntegrationResponse)
def commercial_entra_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    return _entra_status_impl(org_id, tool_id, session, cloud=NationalCloud.COMMERCIAL)


@gcc_high_router.post("/refresh-tokens", response_model=EntraRefreshTokensResponse)
def gcc_entra_refresh_tokens(
    payload: EntraRefreshTokensBody, session: Session = Depends(get_db)
) -> EntraRefreshTokensResponse:
    return _entra_refresh_impl(payload, session, cloud=NationalCloud.GCC_HIGH)


@gcc_high_router.get("/flow", response_model=EntraFlowResponse)
def gcc_entra_flow(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> EntraFlowResponse:
    return _entra_flow_impl(org_id, tool_id, session, cloud=NationalCloud.GCC_HIGH)


@gcc_high_router.get("/status", response_model=ToolIntegrationResponse)
def gcc_entra_status(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> ToolIntegrationResponse:
    return _entra_status_impl(org_id, tool_id, session, cloud=NationalCloud.GCC_HIGH)
