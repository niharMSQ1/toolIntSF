from __future__ import annotations

from typing import Any

from app.integrations.categories.project_management.common_schema import UnifiedProject, UnifiedTask, UnifiedUser


def notion_user_to_unified(raw: dict[str, Any]) -> UnifiedUser:
    uid = str(raw.get("id") or "")
    name = raw.get("name") if isinstance(raw.get("name"), str) else None
    return UnifiedUser(id=uid, name=name, email=None, provider="notion", raw={"id": uid, "type": raw.get("type")})


def notion_page_to_unified_task(raw: dict[str, Any]) -> UnifiedTask:
    """Map a database page or block-backed page to UnifiedTask when used as work item."""
    pid = str(raw.get("id") or "")
    props = raw.get("properties")
    title = None
    if isinstance(props, dict):
        for _k, v in props.items():
            if isinstance(v, dict) and v.get("type") == "title":
                ta = v.get("title")
                if isinstance(ta, list) and ta and isinstance(ta[0], dict):
                    title = ta[0].get("plain_text")
                break
    return UnifiedTask(
        id=pid,
        name=title if isinstance(title, str) else None,
        completed=None,
        due_on=None,
        due_at=None,
        assignee_user_id=None,
        project_ids=[],
        status=None,
        permalink_url=raw.get("url") if isinstance(raw.get("url"), str) else None,
        provider="notion",
        raw={"id": pid, "object": raw.get("object")},
    )


def notion_page_to_unified_project(raw: dict[str, Any]) -> UnifiedProject:
    pid = str(raw.get("id") or "")
    title = None
    props = raw.get("properties")
    if isinstance(props, dict):
        for _k, v in props.items():
            if isinstance(v, dict) and v.get("type") == "title":
                ta = v.get("title")
                if isinstance(ta, list) and ta and isinstance(ta[0], dict):
                    title = ta[0].get("plain_text")
                break
    return UnifiedProject(
        id=pid,
        name=title if isinstance(title, str) else None,
        provider="notion",
        archived=raw.get("archived") if isinstance(raw.get("archived"), bool) else None,
        permalink_url=raw.get("url") if isinstance(raw.get("url"), str) else None,
        raw={"id": pid},
    )
