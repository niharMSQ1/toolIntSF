"""Microsoft Entra OAuth: commercial + GCC High authorize and callback routes."""

from __future__ import annotations

from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.integrations.categories.idp.microsoft_entra.collection_runner import (
    run_entra_evidence_collection_after_oauth_background,
)
from app.integrations.categories.idp.microsoft_entra.credentials import (
    resolve_national_cloud,
    resolve_oauth_application_credentials,
    resolve_redirect_uri,
    resolve_scopes,
    resolve_tenant_id,
)
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud
from app.integrations.categories.idp.microsoft_entra.oauth import (
    build_authorization_url,
    build_state,
    exchange_code_for_tokens,
    merge_token_response_into_config,
    parse_state,
)
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import AuthorizeResponse, EntraOAuthCallbackResponse

router = APIRouter(tags=["oauth", "idp", "microsoft_entra"])


def _ui_redirect(base_url: str, **query: str) -> RedirectResponse:
    u = base_url.strip()
    if not query:
        return RedirectResponse(u, status_code=302)
    q = urlencode(query)
    sep = "&" if "?" in u else "?"
    return RedirectResponse(f"{u}{sep}{q}", status_code=302)


def _user_id_for_collection(row: dict[str, Any], cfg: dict[str, Any]) -> str | None:
    if row.get("user_id") is not None:
        return str(row["user_id"])
    raw = cfg.get("user_id")
    if raw is not None and str(raw).strip():
        return str(raw)
    return None


def _entra_authorize_impl(
    org_id: str,
    tool_id: str,
    session: Session,
    *,
    cloud: NationalCloud,
) -> AuthorizeResponse:
    settings = get_settings()
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Configure integration first (POST .../configure).")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data in DB")
    if resolve_national_cloud(cfg) != cloud:
        raise HTTPException(
            status_code=400,
            detail="Integration national_cloud does not match this authorize URL (use entra vs entra-gcc-high).",
        )
    try:
        client_id, _secret = resolve_oauth_application_credentials(cfg, settings=settings, cloud=cloud)
        redir = resolve_redirect_uri(cfg, settings=settings, cloud=cloud)
        tenant = resolve_tenant_id(cfg)
        scopes = resolve_scopes(cfg, cloud=cloud)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(org_id, tool_id)
    url = build_authorization_url(
        client_id=client_id,
        redirect_uri=redir,
        tenant_id=tenant,
        state=state,
        cloud=cloud,
        scopes=scopes,
    )
    return AuthorizeResponse(authorization_url=url, state=state)


def _entra_oauth_callback_impl(
    code: str,
    state: str,
    session: Session,
    background_tasks: BackgroundTasks,
    *,
    cloud: NationalCloud,
    error: str | None,
) -> RedirectResponse | EntraOAuthCallbackResponse:
    settings = get_settings()
    ui_base = (settings.post_oauth_success_redirect_url or "").strip()

    def _success_json_or_redirect(
        *,
        organization_id: str,
        tool_id: str,
        collection_started: bool,
        next_step: str,
    ) -> RedirectResponse | EntraOAuthCallbackResponse:
        if ui_base:
            return _ui_redirect(ui_base)
        return EntraOAuthCallbackResponse(
            ok=True,
            organization_id=organization_id,
            tool_id=tool_id,
            message="OAuth tokens stored on tool_integrations.",
            collection_started=collection_started,
            next_step=next_step,
            collect_post_json_example=None,
        )

    if error:
        if ui_base:
            return _ui_redirect(ui_base, oauth_error=str(error))
        raise HTTPException(status_code=400, detail={"error": error})
    try:
        parsed = parse_state(state)
    except (ValueError, KeyError) as e:
        if ui_base:
            return _ui_redirect(ui_base, oauth_error="invalid_state", detail=str(e)[:200])
        raise HTTPException(status_code=400, detail=f"Invalid state: {e}") from e

    org_id = parsed["org_id"]
    tool_id = parsed["tool_id"]
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        if ui_base:
            return _ui_redirect(ui_base, oauth_error="integration_not_found")
        raise HTTPException(status_code=404, detail="Integration not found")

    cfg = dict(row["configuration_data"])
    if resolve_national_cloud(cfg) != cloud:
        if ui_base:
            return _ui_redirect(ui_base, oauth_error="cloud_mismatch")
        raise HTTPException(
            status_code=400,
            detail="Integration national_cloud does not match this callback URL.",
        )

    try:
        tenant = resolve_tenant_id(cfg)
        redir = resolve_redirect_uri(cfg, settings=settings, cloud=cloud)
        client_id, client_secret = resolve_oauth_application_credentials(cfg, settings=settings, cloud=cloud)
        scopes = resolve_scopes(cfg, cloud=cloud)
    except ValueError as e:
        if ui_base:
            return _ui_redirect(ui_base, oauth_error="config_error", detail=str(e)[:200])
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        token_payload = exchange_code_for_tokens(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redir,
            code=code,
            tenant_id=tenant,
            cloud=cloud,
            scopes=scopes,
        )
    except Exception as e:  # noqa: BLE001
        if ui_base:
            return _ui_redirect(ui_base, oauth_error="token_exchange_failed", detail=str(e)[:200])
        raise HTTPException(status_code=400, detail=str(e)) from e

    new_cfg = merge_token_response_into_config(
        cfg,
        token_payload,
        tenant_id=tenant,
        cloud=cloud,
    )
    persistence.save_tool_integration_config(session, row["id"], new_cfg)

    user_id_str = _user_id_for_collection(row, new_cfg)
    collection_started = False
    if user_id_str:
        background_tasks.add_task(
            run_entra_evidence_collection_after_oauth_background,
            org_id,
            tool_id,
            user_id_str,
        )
        collection_started = True

    if collection_started:
        next_msg = "OAuth complete. Evidence collection from Microsoft Graph is running automatically in the background."
    else:
        next_msg = (
            "OAuth tokens saved, but automatic evidence collection was skipped because user_id is missing. "
            "POST /configure again with top-level user_id, then complete OAuth again."
        )

    return _success_json_or_redirect(
        organization_id=org_id,
        tool_id=tool_id,
        collection_started=collection_started,
        next_step=next_msg,
    )


@router.get("/api/v1/oauth/entra/authorize", response_model=AuthorizeResponse)
def entra_authorize_commercial(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> AuthorizeResponse:
    return _entra_authorize_impl(org_id, tool_id, session, cloud=NationalCloud.COMMERCIAL)


@router.get("/api/v1/oauth/entra-gcc-high/authorize", response_model=AuthorizeResponse)
def entra_authorize_gcc_high(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> AuthorizeResponse:
    return _entra_authorize_impl(org_id, tool_id, session, cloud=NationalCloud.GCC_HIGH)


@router.get("/idp/entra/callback")
def entra_oauth_callback_commercial(
    code: str,
    state: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
    error: Annotated[str | None, Query()] = None,
) -> EntraOAuthCallbackResponse:
    return _entra_oauth_callback_impl(
        code, state, session, background_tasks, cloud=NationalCloud.COMMERCIAL, error=error
    )


@router.get("/idp/entra-gcc-high/callback")
def entra_oauth_callback_gcc_high(
    code: str,
    state: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
    error: Annotated[str | None, Query()] = None,
) -> EntraOAuthCallbackResponse:
    return _entra_oauth_callback_impl(
        code, state, session, background_tasks, cloud=NationalCloud.GCC_HIGH, error=error
    )
