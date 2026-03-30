"""Azure DevOps: normalized data routes."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.azure_devops import api_client
from app.integrations.categories.devtools.azure_devops.normalize import (
    ado_artifact_to_unified,
    ado_build_to_unified,
    ado_commit_to_unified,
    ado_connection_user_to_unified,
    ado_pr_to_unified,
    ado_ref_to_unified,
    ado_repo_to_unified,
    ado_timeline_record_to_job,
)
from app.integrations.categories.devtools.azure_devops.session import get_api_context, require_project

router = APIRouter(prefix="/api/v1/integrations/devtools/azure-devops", tags=["integrations", "devtools", "azure-devops"])


def _project(ctx: dict, project: str | None) -> str:
    if project and str(project).strip():
        return str(project).strip()
    return require_project(ctx)


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    pat = ctx["pat"]
    base_url = ctx["base_url"]
    organization = ctx["organization"]
    api_version = ctx["api_version"]
    try:
        raw = api_client.get_connection_data(base_url, organization, pat, api_version=api_version)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    user = ado_connection_user_to_unified(raw if isinstance(raw, dict) else {})
    return {"unified": user.model_dump(), "raw": raw}


@router.get("/projects")
def projects(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        rows = api_client.list_projects(ctx["base_url"], ctx["organization"], ctx["pat"], api_version=ctx["api_version"])
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {"projects": rows}


@router.get("/repos")
def list_repos(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    proj = _project(ctx, project)
    try:
        rows = api_client.list_repositories(
            ctx["base_url"],
            ctx["organization"],
            proj,
            ctx["pat"],
            api_version=ctx["api_version"],
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    web_base = ctx["base_url"]
    org = ctx["organization"]
    unified = [ado_repo_to_unified(r, web_base=web_base, organization=org, project=proj).model_dump() for r in rows]
    return {"unified_repositories": unified, "raw_repositories": rows}


@router.get("/repos/{repo_id}")
def get_repo(
    repo_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    proj = _project(ctx, project)
    try:
        raw = api_client.get_repository(
            ctx["base_url"],
            ctx["organization"],
            proj,
            repo_id,
            ctx["pat"],
            api_version=ctx["api_version"],
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = ado_repo_to_unified(
        raw,
        web_base=ctx["base_url"],
        organization=ctx["organization"],
        project=proj,
    )
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/repos/{repo_id}/commits")
def commits(
    repo_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    proj = _project(ctx, project)
    try:
        rows = api_client.list_commits(
            ctx["base_url"],
            ctx["organization"],
            proj,
            repo_id,
            ctx["pat"],
            api_version=ctx["api_version"],
            max_items=limit,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_commits": [ado_commit_to_unified(r).model_dump() for r in rows],
        "raw_commits": rows,
    }


@router.get("/repos/{repo_id}/branches")
def branches(
    repo_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
    limit: int = 100,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    proj = _project(ctx, project)
    try:
        rows = api_client.list_refs_heads(
            ctx["base_url"],
            ctx["organization"],
            proj,
            repo_id,
            ctx["pat"],
            api_version=ctx["api_version"],
            max_items=limit,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_branches": [ado_ref_to_unified(r).model_dump() for r in rows],
        "raw_refs": rows,
    }


@router.get("/pullrequests")
def pullrequests(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    proj = _project(ctx, project)
    try:
        rows = api_client.list_pull_requests(
            ctx["base_url"],
            ctx["organization"],
            proj,
            ctx["pat"],
            api_version=ctx["api_version"],
            max_items=limit,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_pull_requests": [ado_pr_to_unified(r).model_dump() for r in rows],
        "raw_pull_requests": rows,
    }


@router.get("/builds")
def builds(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
    limit: int = 30,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    proj = _project(ctx, project)
    try:
        rows = api_client.list_builds(
            ctx["base_url"],
            ctx["organization"],
            proj,
            ctx["pat"],
            api_version=ctx["api_version"],
            max_items=limit,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    web_base = ctx["base_url"]
    org = ctx["organization"]
    unified = [
        ado_build_to_unified(r, web_base=web_base, organization=org, project=proj).model_dump() for r in rows
    ]
    return {"unified_pipelines": unified, "raw_builds": rows}


@router.get("/builds/{build_id}/jobs")
def build_jobs(
    build_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    proj = _project(ctx, project)
    try:
        raw = api_client.get_build_timeline(
            ctx["base_url"],
            ctx["organization"],
            proj,
            build_id,
            ctx["pat"],
            api_version=ctx["api_version"],
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    records = raw.get("records") if isinstance(raw, dict) else None
    jobs: list[dict[str, object]] = []
    if isinstance(records, list):
        for rec in records:
            if isinstance(rec, dict):
                j = ado_timeline_record_to_job(rec)
                if j:
                    jobs.append(j.model_dump())
    return {"unified_jobs": jobs, "raw_timeline": raw}


@router.get("/builds/{build_id}/artifacts")
def build_artifacts(
    build_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    project: str | None = None,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    proj = _project(ctx, project)
    try:
        rows = api_client.list_build_artifacts(
            ctx["base_url"],
            ctx["organization"],
            proj,
            build_id,
            ctx["pat"],
            api_version=ctx["api_version"],
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_artifacts": [ado_artifact_to_unified(r).model_dump() for r in rows],
        "raw_artifacts": rows,
    }
