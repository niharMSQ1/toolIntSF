"""Jira Cloud OAuth authorize + callback routes."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.integrations.categories.itsm.jira import api_client
from app.integrations.categories.itsm.jira.collection_runner import (
    run_jira_evidence_collection_after_oauth_background,
)
from app.integrations.categories.itsm.jira.credentials import resolve_oauth_credentials, resolve_redirect_uri
from app.integrations.categories.itsm.jira.oauth import (
    build_authorization_url,
    build_state,
    exchange_code_for_tokens,
    merge_token_response_into_config,
    parse_state,
)
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import AuthorizeResponse, JiraOAuthCallbackResponse

router = APIRouter(tags=["oauth", "itsm", "jira"])


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


@router.get("/api/v1/oauth/jira/authorize", response_model=AuthorizeResponse)
def jira_authorize(
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
        client_id, _secret = resolve_oauth_credentials(cfg)
        redir = resolve_redirect_uri(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    state = build_state(org_id, tool_id)
    url = build_authorization_url(
        client_id=client_id,
        redirect_uri=redir,
        state=state,
    )
    return AuthorizeResponse(authorization_url=url, state=state)


def _jira_oauth_callback_impl(
    code: str,
    state: str,
    session: Session,
    background_tasks: BackgroundTasks,
    *,
    error: str | None,
) -> RedirectResponse | JiraOAuthCallbackResponse:
    settings = get_settings()
    ui_base = (settings.post_oauth_success_redirect_url or "").strip()

    def _success_json_or_redirect(
        *,
        organization_id: str,
        tool_id: str,
        collection_started: bool,
        next_step: str,
    ) -> RedirectResponse | JiraOAuthCallbackResponse:
        if ui_base:
            return _ui_redirect(ui_base)
        return JiraOAuthCallbackResponse(
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
    access = new_cfg.get("access_token")
    if access:
        try:
            resources = api_client.list_accessible_resources(str(access))
            cid, site_url = api_client.pick_jira_cloud_id(resources)
            if cid:
                new_cfg["atlassian_cloud_id"] = cid
                if site_url:
                    new_cfg["atlassian_site_url"] = site_url
                new_cfg["atlassian_accessible_resources"] = resources[:25]
        except Exception:
            # Cloud id can be resolved on first collect via ensure_cloud_id_in_config.
            pass

    persistence.save_tool_integration_config(session, row["id"], new_cfg)

    user_id_str = _user_id_for_collection(row, new_cfg)
    collection_started = False
    if user_id_str:
        background_tasks.add_task(
            run_jira_evidence_collection_after_oauth_background,
            org_id,
            tool_id,
            user_id_str,
        )
        collection_started = True

    if collection_started:
        next_msg = (
            "OAuth complete. Evidence collection from Jira Cloud is running automatically in the background. "
            "No further action is required."
        )
    else:
        next_msg = (
            "OAuth tokens saved, but automatic evidence collection was skipped because user_id is missing. "
            "POST /configure again with top-level user_id (so tool_integrations.user_id is set), then complete OAuth again."
        )

    return _success_json_or_redirect(
        organization_id=org_id,
        tool_id=tool_id,
        collection_started=collection_started,
        next_step=next_msg,
    )


@router.get("/itsm/jira/callback", response_model=None)
def jira_oauth_callback(
    code: str,
    state: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
    error: str | None = None,
) -> RedirectResponse | JiraOAuthCallbackResponse:
    return _jira_oauth_callback_impl(code, state, session, background_tasks, error=error)
