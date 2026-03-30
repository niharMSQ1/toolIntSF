from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.linear import api_client
from app.integrations.categories.project_management.linear.normalize import (
    linear_issue_to_unified,
    linear_project_to_unified,
    linear_viewer_to_unified,
)
from app.integrations.categories.project_management.linear.session import get_key

router = APIRouter(prefix="/api/v1/integrations/project-management/linear", tags=["integrations", "project-management", "linear"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    key = get_key(session, org_id, tool_id)
    raw = api_client.get_viewer(key)
    if not raw:
        return {"unified": {}, "raw": {}}
    return {"unified": linear_viewer_to_unified(raw).model_dump(), "raw": raw}


@router.get("/issues")
def issues(org_id: str, tool_id: str, session: Session = Depends(get_db), first: int = 50) -> dict[str, object]:
    key = get_key(session, org_id, tool_id)
    rows = api_client.list_issues(key, first=first)
    return {"unified_tasks": [linear_issue_to_unified(r).model_dump() for r in rows], "raw_issues": rows}


@router.get("/projects")
def projects(org_id: str, tool_id: str, session: Session = Depends(get_db), first: int = 50) -> dict[str, object]:
    key = get_key(session, org_id, tool_id)
    rows = api_client.list_projects(key, first=first)
    return {"unified_projects": [linear_project_to_unified(r).model_dump() for r in rows], "raw_projects": rows}
