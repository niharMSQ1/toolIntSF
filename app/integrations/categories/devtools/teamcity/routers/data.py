"""TeamCity: server, projects, builds, artifacts."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.teamcity import api_client
from app.integrations.categories.devtools.teamcity.normalize import (
    teamcity_artifact_to_unified,
    teamcity_build_to_pipeline,
    teamcity_project_to_repo,
    teamcity_server_to_user,
)
from app.integrations.categories.devtools.teamcity.session import get_api_context

router = APIRouter(prefix="/api/v1/integrations/devtools/teamcity", tags=["integrations", "devtools", "teamcity"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_server(ctx["base_url"], ctx["token"])
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = teamcity_server_to_user(raw if isinstance(raw, dict) else {})
    return {"unified": u.model_dump(), "note": "Identity stub from /app/rest/server; map to DevOpsUser.", "raw": raw}


@router.get("/projects")
def projects(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        rows = api_client.list_projects(ctx["base_url"], ctx["token"])
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    base = ctx["base_url"]
    return {
        "unified_repositories": [teamcity_project_to_repo(r, base_url=base).model_dump() for r in rows],
        "raw_projects": rows,
    }


@router.get("/builds")
def builds(org_id: str, tool_id: str, session: Session = Depends(get_db), limit: int = 20) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        rows = api_client.list_builds(ctx["base_url"], ctx["token"], count=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    base = ctx["base_url"]
    return {
        "unified_pipelines": [teamcity_build_to_pipeline(r, base_url=base).model_dump() for r in rows],
        "raw_builds": rows,
    }


@router.get("/builds/{build_id}")
def build_detail(
    build_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_build(ctx["base_url"], ctx["token"], build_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = teamcity_build_to_pipeline(raw if isinstance(raw, dict) else {}, base_url=ctx["base_url"])
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/builds/{build_id}/artifacts")
def build_artifacts(
    build_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        rows = api_client.get_build_artifacts(ctx["base_url"], ctx["token"], build_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_artifacts": [teamcity_artifact_to_unified(r).model_dump() for r in rows],
        "raw_artifacts": rows,
    }
