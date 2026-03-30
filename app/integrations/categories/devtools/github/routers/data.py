"""GitHub: normalized data endpoints (owner/repo path parameters)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.github import api_client
from app.integrations.categories.devtools.github.normalize import (
    github_artifact_to_unified,
    github_branch_to_unified,
    github_commit_list_item_to_unified,
    github_job_to_unified,
    github_pull_to_unified,
    github_repo_to_unified,
    github_user_to_unified,
    github_workflow_run_to_unified,
)
from app.integrations.categories.devtools.github.session import get_token

router = APIRouter(prefix="/api/v1/integrations/devtools/github", tags=["integrations", "devtools", "github"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    try:
        raw = api_client.get_user(token)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {"unified": github_user_to_unified(raw).model_dump(), "raw": raw}


@router.get("/repos/{owner}/{repo}")
def repository(
    owner: str,
    repo: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    try:
        raw = api_client.get_repository(owner, repo, token)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {"unified": github_repo_to_unified(raw).model_dump(), "raw": raw}


@router.get("/repos/{owner}/{repo}/commits")
def commits(
    owner: str,
    repo: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    try:
        rows = api_client.list_commits(owner, repo, token, max_items=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_commits": [github_commit_list_item_to_unified(r).model_dump() for r in rows],
        "raw_commits": rows,
    }


@router.get("/repos/{owner}/{repo}/branches")
def branches(
    owner: str,
    repo: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    try:
        rows = api_client.list_branches(owner, repo, token, max_items=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_branches": [github_branch_to_unified(r).model_dump() for r in rows],
        "raw_branches": rows,
    }


@router.get("/repos/{owner}/{repo}/pulls")
def pulls(
    owner: str,
    repo: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    state: str = "open",
    limit: int = 50,
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    try:
        rows = api_client.list_pull_requests(owner, repo, token, state=state, max_items=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_pull_requests": [github_pull_to_unified(r).model_dump() for r in rows],
        "raw_pulls": rows,
    }


@router.get("/repos/{owner}/{repo}/actions/runs")
def workflow_runs(
    owner: str,
    repo: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 30,
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    try:
        rows = api_client.list_workflow_runs(owner, repo, token, max_items=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_pipelines": [github_workflow_run_to_unified(r).model_dump() for r in rows],
        "raw_workflow_runs": rows,
    }


@router.get("/repos/{owner}/{repo}/actions/runs/{run_id}/jobs")
def workflow_jobs(
    owner: str,
    repo: str,
    run_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    try:
        rows = api_client.list_jobs_for_run(owner, repo, run_id, token)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_jobs": [github_job_to_unified(r).model_dump() for r in rows],
        "raw_jobs": rows,
    }


@router.get("/repos/{owner}/{repo}/actions/artifacts")
def artifacts(
    owner: str,
    repo: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 30,
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    try:
        rows = api_client.list_artifacts(owner, repo, token, max_items=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_artifacts": [github_artifact_to_unified(r).model_dump() for r in rows],
        "raw_artifacts": rows,
    }
