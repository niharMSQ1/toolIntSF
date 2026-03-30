"""Map Microsoft Graph Planner JSON to unified schema."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.project_management.common_schema import (
    UnifiedProject,
    UnifiedStatus,
    UnifiedTask,
    UnifiedUser,
)


def graph_user_to_unified(raw: dict[str, Any]) -> UnifiedUser:
    uid = str(raw.get("id") or "")
    mail = raw.get("mail")
    upn = raw.get("userPrincipalName")
    email = mail if isinstance(mail, str) else (upn if isinstance(upn, str) else None)
    return UnifiedUser(
        id=uid,
        name=raw.get("displayName") if isinstance(raw.get("displayName"), str) else None,
        email=email,
        provider="microsoft_planner",
        raw={"id": uid},
    )


def planner_plan_to_unified(raw: dict[str, Any]) -> UnifiedProject:
    pid = str(raw.get("id") or "")
    return UnifiedProject(
        id=pid,
        name=raw.get("title") if isinstance(raw.get("title"), str) else None,
        provider="microsoft_planner",
        archived=None,
        permalink_url=None,
        raw={"id": pid, "owner": raw.get("owner")},
    )


def planner_task_to_unified(raw: dict[str, Any], *, plan_id: str) -> UnifiedTask:
    tid = str(raw.get("id") or "")
    pct = raw.get("percentComplete")
    completed = int(pct) == 100 if pct is not None else None
    assignments = raw.get("assignments")
    assignee_id = None
    if isinstance(assignments, dict) and assignments:
        assignee_id = next(iter(assignments.keys()), None)
    bucket_id = raw.get("bucketId")
    st = UnifiedStatus(label=str(bucket_id) if bucket_id else None, resource_type="bucket", provider="microsoft_planner")
    return UnifiedTask(
        id=tid,
        name=raw.get("title") if isinstance(raw.get("title"), str) else None,
        completed=completed,
        due_on=raw.get("dueDateTime")[:10] if isinstance(raw.get("dueDateTime"), str) else None,
        due_at=raw.get("dueDateTime") if isinstance(raw.get("dueDateTime"), str) else None,
        assignee_user_id=str(assignee_id) if assignee_id else None,
        project_ids=[plan_id],
        status=st,
        permalink_url=None,
        provider="microsoft_planner",
        raw={"id": tid, "planId": raw.get("planId")},
    )
