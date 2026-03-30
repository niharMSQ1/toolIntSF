"""Jenkins: jobs, builds, Pipeline stages, artifacts (mapped to unified schema)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.jenkins import api_client
from app.integrations.categories.devtools.jenkins.normalize import (
    jenkins_artifact_to_unified,
    jenkins_build_to_pipeline,
    jenkins_job_to_repository,
    jenkins_user_to_unified,
    jenkins_wfapi_stage_to_job,
)
from app.integrations.categories.devtools.jenkins.session import collect_wf_stages, get_api_context

router = APIRouter(prefix="/api/v1/integrations/devtools/jenkins", tags=["integrations", "devtools", "jenkins"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_whoami(ctx["base_url"], ctx["username"], ctx["token"])
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = jenkins_user_to_unified(raw if isinstance(raw, dict) else {}, username=ctx["username"])
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/jobs")
def jobs(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        rows = api_client.list_jobs(ctx["base_url"], ctx["username"], ctx["token"])
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_repositories": [jenkins_job_to_repository(r).model_dump() for r in rows],
        "note": "Jobs are mapped to DevOpsRepository for a single unified view across tools.",
        "raw_jobs": rows,
    }


@router.get("/jobs/{job_path:path}/builds")
def job_builds(
    job_path: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 30,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        rows = api_client.list_builds_for_job(
            ctx["base_url"],
            ctx["username"],
            ctx["token"],
            job_path,
            limit=limit,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    unified = [jenkins_build_to_pipeline(r).model_dump() for r in rows]
    return {"unified_pipelines": unified, "raw_builds": rows}


@router.get("/jobs/{job_path:path}/builds/{build_number}")
def job_build(
    job_path: str,
    build_number: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_build(ctx["base_url"], ctx["username"], ctx["token"], job_path, build_number)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    u = jenkins_build_to_pipeline(raw if isinstance(raw, dict) else {})
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/jobs/{job_path:path}/builds/{build_number}/stages")
def job_build_stages(
    job_path: str,
    build_number: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_wfapi_describe(ctx["base_url"], ctx["username"], ctx["token"], job_path, build_number)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="wfapi/describe not available (non-Pipeline job or plugin missing).",
            ) from e
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    if not isinstance(raw, dict):
        raw = {}
    stages = collect_wf_stages(raw)
    jobs_out = [jenkins_wfapi_stage_to_job(s, i).model_dump() for i, s in enumerate(stages)]
    return {"unified_jobs": jobs_out, "raw_wfapi": raw}


@router.get("/jobs/{job_path:path}/builds/{build_number}/artifacts")
def job_build_artifacts(
    job_path: str,
    build_number: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_build(ctx["base_url"], ctx["username"], ctx["token"], job_path, build_number)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    arts = raw.get("artifacts") if isinstance(raw, dict) else None
    if not isinstance(arts, list):
        arts = []
    build_url = raw.get("url") if isinstance(raw.get("url"), str) else None
    return {
        "unified_artifacts": [jenkins_artifact_to_unified(a, build_url=build_url).model_dump() for a in arts if isinstance(a, dict)],
        "raw_artifacts": arts,
    }
