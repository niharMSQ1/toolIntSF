from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.clickup import api_client
from app.integrations.categories.project_management.clickup.normalize import cu_task_to_unified, cu_user_to_unified
from app.integrations.categories.project_management.clickup.session import get_token

router = APIRouter(prefix="/api/v1/integrations/project-management/clickup", tags=["integrations", "project-management", "clickup"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    raw = api_client.get_user(token)
    u = raw.get("user")
    if not isinstance(u, dict):
        return {"unified": {}, "raw": raw}
    return {"unified": cu_user_to_unified(u).model_dump(), "raw": raw}


@router.get("/teams")
def teams(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    return {"teams": api_client.get_teams(token)}


@router.get("/lists/{list_id}/tasks")
def list_tasks(list_id: str, org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    rows = api_client.get_list_tasks(token, list_id)
    return {
        "unified_tasks": [cu_task_to_unified(r, list_id=list_id).model_dump() for r in rows],
        "raw_tasks": rows,
    }
