from __future__ import annotations

from typing import Any

from app.integrations.categories.project_management.common_schema import UnifiedProject, UnifiedStatus, UnifiedTask, UnifiedUser


def linear_viewer_to_unified(raw: dict[str, Any]) -> UnifiedUser:
    uid = str(raw.get("id") or "")
    return UnifiedUser(
        id=uid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        email=raw.get("email") if isinstance(raw.get("email"), str) else None,
        provider="linear",
        raw={"id": uid},
    )


def linear_project_to_unified(raw: dict[str, Any]) -> UnifiedProject:
    pid = str(raw.get("id") or "")
    return UnifiedProject(
        id=pid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        provider="linear",
        archived=None,
        permalink_url=raw.get("url") if isinstance(raw.get("url"), str) else None,
        raw={"id": pid},
    )


def linear_issue_to_unified(raw: dict[str, Any]) -> UnifiedTask:
    iid = str(raw.get("id") or "")
    st_obj = raw.get("state")
    st = None
    if isinstance(st_obj, dict) and isinstance(st_obj.get("name"), str):
        st = UnifiedStatus(label=st_obj["name"], resource_type="workflowState", provider="linear")
    return UnifiedTask(
        id=iid,
        name=raw.get("title") if isinstance(raw.get("title"), str) else None,
        completed=None,
        due_on=None,
        due_at=None,
        assignee_user_id=None,
        project_ids=[],
        status=st,
        permalink_url=raw.get("url") if isinstance(raw.get("url"), str) else None,
        provider="linear",
        raw={"id": iid, "identifier": raw.get("identifier")},
    )
