"""GitHub OAuth App: authorize URL and callback."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.integrations.categories.devtools.github.credentials import resolve_oauth_credentials, resolve_redirect_uri
from app.integrations.categories.devtools.github.oauth import (
    build_authorization_url,
    build_state,
    exchange_code_for_token,
    merge_token_into_config,
    parse_state,
)
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import AuthorizeResponse, GitHubOAuthCallbackResponse

oauth_authorize_router = APIRouter(prefix="/api/v1/oauth/github", tags=["oauth", "devtools", "github"])

callback_router = APIRouter(
    prefix="/api/v1/integrations/devtools/github",
    tags=["oauth", "devtools", "github"],
)


def _ui_redirect(base_url: str, **query: str) -> RedirectResponse:
    u = base_url.strip()
    if not query:
        return RedirectResponse(u, status_code=302)
    q = urlencode(query)
    sep = "&" if "?" in u else "?"
    return RedirectResponse(f"{u}{sep}{q}", status_code=302)


@oauth_authorize_router.get("/authorize", response_model=AuthorizeResponse)
def github_authorize(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> AuthorizeResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Configure integration first (POST .../configure).")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data in DB")
    try:
        client_id, _s = resolve_oauth_credentials(cfg)
        redir = resolve_redirect_uri(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(org_id, tool_id)
    url = build_authorization_url(client_id=client_id, redirect_uri=redir, state=state)
    return AuthorizeResponse(authorization_url=url, state=state)


@callback_router.get("/oauth/callback", response_model=None)
def github_oauth_callback(
    code: str,
    state: str,
    session: Session = Depends(get_db),
    error: str | None = None,
) -> RedirectResponse | GitHubOAuthCallbackResponse:
    settings = get_settings()
    ui_base = (settings.post_oauth_success_redirect_url or "").strip()

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
        client_id, client_secret = resolve_oauth_credentials(cfg)
        redir = resolve_redirect_uri(cfg)
    except ValueError as e:
        if ui_base:
            return _ui_redirect(ui_base, oauth_error="config_error", detail=str(e)[:200])
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        token_payload = exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redir,
            code=code,
        )
    except Exception as e:  # noqa: BLE001
        if ui_base:
            return _ui_redirect(ui_base, oauth_error="token_exchange_failed", detail=str(e)[:200])
        raise HTTPException(status_code=400, detail=str(e)) from e

    if "error" in token_payload:
        if ui_base:
            return _ui_redirect(ui_base, oauth_error=str(token_payload.get("error", "oauth_error")))
        raise HTTPException(status_code=400, detail=token_payload)

    new_cfg = merge_token_into_config(cfg, token_payload)
    persistence.save_tool_integration_config(session, row["id"], new_cfg)

    next_step = "OAuth complete. Call GET .../devtools/github/me or repository routes with owner/repo."

    if ui_base:
        return _ui_redirect(ui_base)

    return GitHubOAuthCallbackResponse(
        ok=True,
        organization_id=org_id,
        tool_id=tool_id,
        message="GitHub OAuth token stored.",
        next_step=next_step,
    )
