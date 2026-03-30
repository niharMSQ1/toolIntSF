"""Normalized Asana data API (unified schema)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.asana import api_client
from app.integrations.categories.project_management.asana.normalize import (
    asana_project_to_unified,
    asana_story_to_unified,
    asana_task_to_unified,
    asana_user_to_unified,
)
from app.integrations.categories.project_management.asana.session import get_token_and_config
router = APIRouter(
    prefix="/api/v1/integrations/project-management/asana",
    tags=["integrations", "project-management", "asana"],
)


class AsanaWebhookRegisterBody(BaseModel):
    """Body for POST .../webhooks/register — https://developers.asana.com/reference/createwebhook"""

    resource_gid: str = Field(description="Asana gid of the resource to watch (e.g. project gid).")
    target_url: str = Field(description="Public HTTPS URL of this app's webhook receiver.")
    filters: list[dict[str, Any]] | None = None


@router.get("/me")
def asana_me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, Any]:
    _, token = get_token_and_config(session, org_id, tool_id)
    raw = api_client.get_me(token)
    data = raw.get("data")
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected users/me response.")
    user = asana_user_to_unified(data)
    return {"unified": user.model_dump(), "raw": raw}


@router.get("/workspaces")
def asana_workspaces(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, Any]:
    _, token = get_token_and_config(session, org_id, tool_id)
    rows = api_client.list_workspaces(token)
    return {"workspaces": rows}


@router.get("/projects")
def asana_projects(
    org_id: str,
    tool_id: str,
    workspace_gid: str,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    _, token = get_token_and_config(session, org_id, tool_id)
    rows = api_client.list_projects_for_workspace(token, workspace_gid)
    unified = [asana_project_to_unified(r).model_dump() for r in rows]
    return {"unified_projects": unified, "raw_projects": rows}


@router.get("/projects/{project_gid}")
def asana_project_detail(
    project_gid: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    _, token = get_token_and_config(session, org_id, tool_id)
    row = api_client.get_project(token, project_gid)
    if not row:
        raise HTTPException(status_code=404, detail="Project not found or inaccessible.")
    return {"unified": asana_project_to_unified(row).model_dump(), "raw": row}


@router.get("/tasks")
def asana_tasks(
    org_id: str,
    tool_id: str,
    project_gid: str,
    session: Session = Depends(get_db),
    max_tasks: int = 200,
) -> dict[str, Any]:
    _, token = get_token_and_config(session, org_id, tool_id)
    cap = max(1, min(max_tasks, 2000))
    rows = api_client.list_tasks_for_project(token, project_gid, max_tasks=cap)
    unified = [asana_task_to_unified(r).model_dump() for r in rows]
    return {"unified_tasks": unified, "raw_tasks": rows}


@router.get("/tasks/{task_gid}")
def asana_task_detail(
    task_gid: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    _, token = get_token_and_config(session, org_id, tool_id)
    row = api_client.get_task(token, task_gid)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found or inaccessible.")
    return {"unified": asana_task_to_unified(row).model_dump(), "raw": row}


@router.get("/tasks/{task_gid}/stories")
def asana_task_stories(
    task_gid: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    max_stories: int = 100,
) -> dict[str, Any]:
    _, token = get_token_and_config(session, org_id, tool_id)
    cap = max(1, min(max_stories, 500))
    rows = api_client.list_stories_for_task(token, task_gid, max_stories=cap)
    unified = [asana_story_to_unified(r).model_dump() for r in rows]
    return {"unified_activities": unified, "raw_stories": rows}


@router.get("/users/{user_gid}")
def asana_user(
    user_gid: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    _, token = get_token_and_config(session, org_id, tool_id)
    row = api_client.get_user(token, user_gid)
    if not row:
        raise HTTPException(status_code=404, detail="User not found or inaccessible.")
    u = asana_user_to_unified(row)
    return {"unified": u.model_dump(), "raw": row}


@router.post("/webhooks/register")
def asana_register_webhook(
    body: AsanaWebhookRegisterBody,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a webhook via Asana API (handshake hits your public target_url)."""
    _, token = get_token_and_config(session, org_id, tool_id)
    return api_client.create_webhook(
        token,
        resource_gid=body.resource_gid,
        target_url=body.target_url,
        filters=body.filters,
    )
