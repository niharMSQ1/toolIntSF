"""BambooHR OAuth authorize + callback routes."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.bamboohr.credentials import (
    AUTH_MODE_APP_OAUTH,
    resolve_auth_mode,
    resolve_client_credentials,
    resolve_redirect_uri,
    resolve_subdomain,
)
from app.integrations.categories.hrms.bamboohr.oauth import (
    build_authorization_url,
    build_state,
    exchange_code_for_tokens,
    merge_token_response_into_config,
    parse_state,
)
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import AuthorizeResponse, BambooOAuthCallbackResponse

router = APIRouter(tags=["oauth", "hrms", "bamboohr"])


def _ui_redirect(base_url: str, **query: str) -> RedirectResponse:
    url = base_url.strip()
    if not query:
        return RedirectResponse(url, status_code=302)
    sep = "&" if "?" in url else "?"
    return RedirectResponse(f"{url}{sep}{urlencode(query)}", status_code=302)


@router.get("/api/v1/oauth/bamboohr/authorize", response_model=AuthorizeResponse)
@router.get("/api/v1/integrations/bamboohr/connect", response_model=AuthorizeResponse)
def bamboohr_authorize(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> AuthorizeResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Configure integration first (POST .../configure).")

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data in DB")

    try:
        if resolve_auth_mode(cfg) != AUTH_MODE_APP_OAUTH:
            raise ValueError("BambooHR connect route only applies when auth_mode is 'app_oauth'.")
        client_id, _secret = resolve_client_credentials(cfg)
        redirect_uri = resolve_redirect_uri(cfg)
        company_domain = resolve_subdomain(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    state = build_state(org_id, tool_id)
    auth_url = build_authorization_url(
        company_domain=company_domain,
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
    )
    return AuthorizeResponse(authorization_url=auth_url, state=state)


@router.get("/hrms/bamboohr/callback", response_model=None)
@router.get("/integrations/bamboohr/callback", response_model=None)
def bamboohr_oauth_callback(
    code: str,
    state: str,
    session: Session = Depends(get_db),
    error: str | None = None,
) -> BambooOAuthCallbackResponse | RedirectResponse:
    ui_base = ""

    if error:
        if ui_base:
            return _ui_redirect(ui_base, oauth_error=str(error))
        raise HTTPException(status_code=400, detail={"error": error})

    try:
        parsed = parse_state(state)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid state: {e}") from e

    org_id = parsed["org_id"]
    tool_id = parsed["tool_id"]
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")

    cfg = dict(row["configuration_data"])
    try:
        if resolve_auth_mode(cfg) != AUTH_MODE_APP_OAUTH:
            raise ValueError("BambooHR callback only applies when auth_mode is 'app_oauth'.")
        company_domain = resolve_subdomain(cfg)
        client_id, client_secret = resolve_client_credentials(cfg)
        redirect_uri = resolve_redirect_uri(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        token_payload = exchange_code_for_tokens(
            company_domain=company_domain,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            code=code,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e)) from e

    new_cfg = merge_token_response_into_config(cfg, token_payload)
    persistence.save_tool_integration_config(session, row["id"], new_cfg)

    return BambooOAuthCallbackResponse(
        ok=True,
        organization_id=org_id,
        tool_id=tool_id,
        message="BambooHR OAuth tokens stored on tool_integrations.",
        next_step="BambooHR app auth is complete. You can now use employee preview routes or POST /api/v1/evidence/bamboohr/collect.",
    )
