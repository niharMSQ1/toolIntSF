from __future__ import annotations

from typing import Any

from app.integrations.categories.project_management.common_schema import (
    UnifiedProject,
    UnifiedStatus,
    UnifiedTask,
    UnifiedUser,
)


def cu_user_to_unified(raw: dict[str, Any]) -> UnifiedUser:
    uid = str(raw.get("id") or "")
    return UnifiedUser(
        id=uid,
        name=raw.get("username") if isinstance(raw.get("username"), str) else None,
        email=raw.get("email") if isinstance(raw.get("email"), str) else None,
        provider="clickup",
        raw={"id": uid},
    )


def cu_list_to_unified(raw: dict[str, Any], *, space_id: str | None = None) -> UnifiedProject:
    lid = str(raw.get("id") or "")
    return UnifiedProject(
        id=lid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        provider="clickup",
        archived=None,
        permalink_url=None,
        raw={"id": lid, "space_id": space_id},
    )


def cu_task_to_unified(raw: dict[str, Any], *, list_id: str) -> UnifiedTask:
    tid = str(raw.get("id") or "")
    status_obj = raw.get("status")
    st = None
    if isinstance(status_obj, dict) and isinstance(status_obj.get("status"), str):
        st = __import__(
            "app.integrations.categories.project_management.common_schema",
            fromlist=["UnifiedStatus"],
        ).UnifiedStatus(label=status_obj["status"], resource_type="status", provider="clickup")
    assignees = raw.get("assignees")
    aid = None
    if isinstance(assignees, list) and assignees and isinstance(assignees[0], dict):
        aid = str(assignees[0].get("id") or "")
    return UnifiedTask(
        id=tid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        completed=raw.get("date_closed") is not None,
        due_on=(
            (dd[:10] if len(dd) >= 10 else None)
            if isinstance((dd := raw.get("due_date")), str)
            else None
        ),
        due_at=raw.get("due_date") if isinstance(raw.get("due_date"), str) else None,
        assignee_user_id=aid,
        project_ids=[list_id],
        status=st,
        permalink_url=raw.get("url") if isinstance(raw.get("url"), str) else None,
        provider="clickup",
        raw={"id": tid},
    )
