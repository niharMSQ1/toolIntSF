"""Map Asana API JSON to unified internal schema."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.project_management.common_schema import (
    UnifiedActivity,
    UnifiedProject,
    UnifiedStatus,
    UnifiedTask,
    UnifiedUser,
)


def _gid(obj: Any) -> str | None:
    if isinstance(obj, dict) and obj.get("gid"):
        return str(obj["gid"])
    return None


def asana_user_to_unified(raw: dict[str, Any]) -> UnifiedUser:
    gid = str(raw.get("gid") or "")
    return UnifiedUser(
        id=gid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        email=raw.get("email") if isinstance(raw.get("email"), str) else None,
        provider="asana",
        raw={"gid": gid, "name": raw.get("name"), "email": raw.get("email")},
    )


def asana_project_to_unified(raw: dict[str, Any]) -> UnifiedProject:
    gid = str(raw.get("gid") or "")
    return UnifiedProject(
        id=gid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        provider="asana",
        archived=bool(raw["archived"]) if "archived" in raw else None,
        permalink_url=raw.get("permalink_url") if isinstance(raw.get("permalink_url"), str) else None,
        raw={"gid": gid, "name": raw.get("name"), "archived": raw.get("archived")},
    )


def _status_from_task(raw: dict[str, Any]) -> UnifiedStatus | None:
    memberships = raw.get("memberships")
    if not isinstance(memberships, list):
        return None
    for m in memberships:
        if not isinstance(m, dict):
            continue
        sec = m.get("section")
        if isinstance(sec, dict):
            name = sec.get("name")
            if isinstance(name, str) and name.strip():
                return UnifiedStatus(label=name, resource_type="section", provider="asana")
    return None


def asana_task_to_unified(raw: dict[str, Any]) -> UnifiedTask:
    gid = str(raw.get("gid") or "")
    assignee = raw.get("assignee")
    assignee_id = _gid(assignee) if isinstance(assignee, dict) else None
    project_ids: list[str] = []
    memberships = raw.get("memberships")
    if isinstance(memberships, list):
        for m in memberships:
            if not isinstance(m, dict):
                continue
            proj = m.get("project")
            if isinstance(proj, dict) and proj.get("gid"):
                project_ids.append(str(proj["gid"]))

    return UnifiedTask(
        id=gid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        completed=bool(raw["completed"]) if "completed" in raw else None,
        due_on=raw.get("due_on") if isinstance(raw.get("due_on"), str) else None,
        due_at=raw.get("due_at") if isinstance(raw.get("due_at"), str) else None,
        assignee_user_id=assignee_id,
        project_ids=project_ids,
        status=_status_from_task(raw),
        permalink_url=raw.get("permalink_url") if isinstance(raw.get("permalink_url"), str) else None,
        provider="asana",
        raw={
            "gid": gid,
            "completed": raw.get("completed"),
            "due_on": raw.get("due_on"),
            "assignee": assignee if isinstance(assignee, dict) else None,
        },
    )


def asana_story_to_unified(raw: dict[str, Any]) -> UnifiedActivity:
    gid = str(raw.get("gid") or "")
    created_by = raw.get("created_by")
    cb_id = _gid(created_by) if isinstance(created_by, dict) else None
    typ = raw.get("type")
    return UnifiedActivity(
        id=gid,
        resource_type="story",
        text=raw.get("text") if isinstance(raw.get("text"), str) else None,
        created_at=raw.get("created_at") if isinstance(raw.get("created_at"), str) else None,
        created_by_user_id=cb_id,
        provider="asana",
        raw={
            "gid": gid,
            "type": typ if isinstance(typ, str) else None,
            "resource_subtype": raw.get("resource_subtype"),
        },
    )
