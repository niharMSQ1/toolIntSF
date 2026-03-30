"""Microsoft Graph Planner data (unified schema)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.microsoft_planner import api_client
from app.integrations.categories.project_management.microsoft_planner.normalize import (
    graph_user_to_unified,
    planner_plan_to_unified,
    planner_task_to_unified,
)
from app.integrations.categories.project_management.microsoft_planner.session import get_token

router = APIRouter(
    prefix="/api/v1/integrations/project-management/microsoft-planner",
    tags=["integrations", "project-management", "microsoft-planner"],
)


@router.get("/me")
def graph_me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    raw = api_client.get_me(token)
    return {"unified": graph_user_to_unified(raw).model_dump(), "raw": raw}


@router.get("/groups/{group_id}/plans")
def list_plans(group_id: str, org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    rows = api_client.list_plans_for_group(token, group_id)
    unified = [planner_plan_to_unified(r).model_dump() for r in rows]
    return {"unified_projects": unified, "raw_plans": rows}


@router.get("/plans/{plan_id}/tasks")
def list_plan_tasks(plan_id: str, org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    rows = api_client.list_tasks_for_plan(token, plan_id)
    unified = [planner_task_to_unified(r, plan_id=plan_id).model_dump() for r in rows]
    return {"unified_tasks": unified, "raw_tasks": rows}


@router.get("/plans/{plan_id}")
def get_plan(plan_id: str, org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    raw = api_client.get_plan(token, plan_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return {"unified": planner_plan_to_unified(raw).model_dump(), "raw": raw}
