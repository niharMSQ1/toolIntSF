"""CircleCI API v2 data routes."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.circleci import api_client
from app.integrations.categories.devtools.circleci.normalize import (
    circleci_me_to_user,
    circleci_pipeline_to_unified,
    circleci_project_to_repo,
    circleci_workflow_job_to_unified,
    circleci_workflow_to_unified,
)
from app.integrations.categories.devtools.circleci.session import get_api_context, project_slug_or_query

router = APIRouter(prefix="/api/v1/integrations/devtools/circleci", tags=["integrations", "devtools", "circleci"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_me(ctx["base_url"], ctx["token"])
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = circleci_me_to_user(raw if isinstance(raw, dict) else {})
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/project")
def project(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    slug = project_slug_or_query(ctx["configuration_data"], project)
    try:
        raw = api_client.get_project(ctx["base_url"], ctx["token"], slug)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = circleci_project_to_repo(raw if isinstance(raw, dict) else {})
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/pipelines")
def pipelines(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
    limit: int = 30,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    slug = project_slug_or_query(ctx["configuration_data"], project)
    try:
        rows = api_client.list_pipelines(ctx["base_url"], ctx["token"], slug, max_items=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_pipelines": [circleci_pipeline_to_unified(r).model_dump() for r in rows],
        "raw_pipelines": rows,
    }


@router.get("/pipelines/{pipeline_id}")
def pipeline_detail(
    pipeline_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_pipeline(ctx["base_url"], ctx["token"], pipeline_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = circleci_pipeline_to_unified(raw if isinstance(raw, dict) else {})
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/workflows/{workflow_id}")
def workflow_detail(
    workflow_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_workflow(ctx["base_url"], ctx["token"], workflow_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = circleci_workflow_to_unified(raw if isinstance(raw, dict) else {})
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/workflows/{workflow_id}/jobs")
def workflow_jobs(
    workflow_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        rows = api_client.list_workflow_jobs(ctx["base_url"], ctx["token"], workflow_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_jobs": [circleci_workflow_job_to_unified(r).model_dump() for r in rows],
        "raw_jobs": rows,
    }
