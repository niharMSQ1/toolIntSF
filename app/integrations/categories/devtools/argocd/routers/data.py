"""Argo CD: applications and account/version."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.argocd import api_client
from app.integrations.categories.devtools.argocd.normalize import (
    argocd_account_to_user,
    argocd_app_to_pipeline,
    argocd_app_to_repository,
    argocd_version_to_user,
)
from app.integrations.categories.devtools.argocd.session import get_api_context

router = APIRouter(prefix="/api/v1/integrations/devtools/argocd", tags=["integrations", "devtools", "argocd"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_account(ctx["base_url"], ctx["token"])
    except httpx.HTTPStatusError:
        try:
            ver = api_client.get_version(ctx["base_url"], ctx["token"])
            u = argocd_version_to_user(ver if isinstance(ver, dict) else {})
        except httpx.HTTPStatusError as e2:
            raise HTTPException(status_code=e2.response.status_code, detail=e2.response.text[:2000]) from e2
        return {"unified": u.model_dump(), "raw": ver, "note": "account endpoint unavailable; returned version as identity stub."}
    u = argocd_account_to_user(raw if isinstance(raw, dict) else {})
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/applications")
def applications(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 100,
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        rows = api_client.list_applications(ctx["base_url"], ctx["token"], limit=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    repos = [argocd_app_to_repository(r).model_dump() for r in rows]
    pipes = [argocd_app_to_pipeline(r).model_dump() for r in rows]
    return {
        "unified_repositories": repos,
        "unified_pipelines": pipes,
        "note": "Each Application maps to both repository (spec.source) and pipeline (status sync/health).",
        "raw_applications": rows,
    }


@router.get("/applications/{name}")
def application_detail(
    name: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    ctx = get_api_context(session, org_id, tool_id)
    try:
        raw = api_client.get_application(ctx["base_url"], ctx["token"], name)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    return {
        "unified_repository": argocd_app_to_repository(raw if isinstance(raw, dict) else {}).model_dump(),
        "unified_pipeline": argocd_app_to_pipeline(raw if isinstance(raw, dict) else {}).model_dump(),
        "raw": raw,
    }
