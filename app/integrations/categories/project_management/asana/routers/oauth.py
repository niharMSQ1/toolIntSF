"""Asana OAuth authorize + callback."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.integrations.categories.project_management.asana.oauth import (
    build_authorization_url,
    build_state,
    exchange_code_for_tokens,
    merge_token_response_into_config,
    parse_state,
)
from app.integrations.categories.project_management.asana.credentials import resolve_oauth_credentials, resolve_redirect_uri
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import AsanaOAuthCallbackResponse, AuthorizeResponse

router = APIRouter(tags=["oauth", "project-management", "asana"])


def _ui_redirect(base_url: str, **query: str) -> RedirectResponse:
    u = base_url.strip()
    if not query:
        return RedirectResponse(u, status_code=302)
    q = urlencode(query)
    sep = "&" if "?" in u else "?"
    return RedirectResponse(f"{u}{sep}{q}", status_code=302)


@router.get("/api/v1/oauth/asana/authorize", response_model=AuthorizeResponse)
def asana_authorize(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> AuthorizeResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Configure integration first (POST .../configure).")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data in DB")
    try:
        client_id, _secret = resolve_oauth_credentials(cfg)
        redir = resolve_redirect_uri(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(org_id, tool_id)
    url = build_authorization_url(client_id=client_id, redirect_uri=redir, state=state)
    return AuthorizeResponse(authorization_url=url, state=state)


def _asana_oauth_callback_impl(
    code: str,
    state: str,
    session: Session,
    *,
    error: str | None,
) -> RedirectResponse | AsanaOAuthCallbackResponse:
    settings = get_settings()
    ui_base = (settings.post_oauth_success_redirect_url or "").strip()

    def _success_json(oid: str, tid: str) -> AsanaOAuthCallbackResponse:
        return AsanaOAuthCallbackResponse(
            ok=True,
            organization_id=oid,
            tool_id=tid,
            message="OAuth tokens stored on tool_integrations.",
            collection_started=False,
            next_step="Call GET /api/v1/integrations/project-management/asana/me to verify access.",
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
    try:
        redir = resolve_redirect_uri(cfg)
        client_id, client_secret = resolve_oauth_credentials(cfg)
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
        )
    except Exception as e:  # noqa: BLE001
        if ui_base:
            return _ui_redirect(ui_base, oauth_error="token_exchange_failed", detail=str(e)[:200])
        raise HTTPException(status_code=400, detail=str(e)) from e

    new_cfg = merge_token_response_into_config(cfg, token_payload)
    persistence.save_tool_integration_config(session, row["id"], new_cfg)

    if ui_base:
        return _ui_redirect(ui_base)
    return _success_json(org_id, tool_id)


@router.get("/project-management/asana/callback", response_model=None)
def asana_oauth_callback(
    code: str,
    state: str,
    session: Session = Depends(get_db),
    error: str | None = None,
) -> RedirectResponse | AsanaOAuthCallbackResponse:
    return _asana_oauth_callback_impl(code, state, session, error=error)
