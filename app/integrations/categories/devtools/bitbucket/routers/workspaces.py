"""List Bitbucket workspaces and persist user selection."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.bitbucket.credentials import (
    has_access_token,
    oauth_complete,
    resolve_access_token,
    resolve_oauth_credentials,
)
from app.integrations.categories.devtools.bitbucket.token_refresh import ensure_fresh_access_token
from app.integrations.categories.devtools.bitbucket.workspaces import fetch_workspaces_for_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import BitbucketSelectWorkspacesBody, BitbucketWorkspacesListResponse

router = APIRouter(
    prefix="/api/v1/integrations/devtools/bitbucket",
    tags=["integrations", "devtools", "bitbucket"],
)


@router.get("/workspaces", response_model=BitbucketWorkspacesListResponse)
def list_workspaces(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> BitbucketWorkspacesListResponse:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = ensure_fresh_access_token(session, row)
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    if not oauth_complete(cfg) or not has_access_token(cfg):
        raise HTTPException(status_code=400, detail="Complete Bitbucket OAuth first.")
    token = resolve_access_token(cfg)
    if not token:
        raise HTTPException(status_code=400, detail="Missing access token.")
    try:
        workspaces = fetch_workspaces_for_token(token)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Bitbucket API error: {e}") from e
    return BitbucketWorkspacesListResponse(workspaces=workspaces)


@router.post("/workspaces", response_model=BitbucketWorkspacesListResponse)
def select_workspaces(body: BitbucketSelectWorkspacesBody, session: Session = Depends(get_db)) -> BitbucketWorkspacesListResponse:
    row = persistence.get_integration(session, body.org_id, body.tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = ensure_fresh_access_token(session, row)
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    if not oauth_complete(cfg):
        raise HTTPException(status_code=400, detail="Complete Bitbucket OAuth first.")

    token = resolve_access_token(cfg)
    if not token:
        raise HTTPException(status_code=400, detail="Missing access token.")

    try:
        available = fetch_workspaces_for_token(token)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Bitbucket API error: {e}") from e

    allowed_slugs = {a["slug"] for a in available if a.get("slug")}
    by_slug = {a["slug"]: a for a in available if a.get("slug")}

    selected: list[dict[str, str]] = []
    for slug in body.workspace_slugs:
        s = str(slug).strip()
        if not s:
            continue
        if s not in allowed_slugs:
            raise HTTPException(
                status_code=400,
                detail=f"Workspace slug {s!r} is not in the list returned by Bitbucket for this token.",
            )
        w = by_slug[s]
        selected.append({"slug": w["slug"], "uuid": w["uuid"], "name": w.get("name", s)})

    if not selected:
        raise HTTPException(status_code=400, detail="Provide at least one valid workspace_slugs entry.")

    new_cfg = dict(cfg)
    new_cfg["selected_workspaces"] = selected
    new_cfg["workspace_selection_completed_at"] = datetime.now(timezone.utc).isoformat()
    persistence.save_tool_integration_config(session, row["id"], new_cfg)

    return BitbucketWorkspacesListResponse(workspaces=selected)
