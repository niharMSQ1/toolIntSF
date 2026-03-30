"""Map Monday.com GraphQL JSON to unified internal schema."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.project_management.common_schema import (
    UnifiedActivity,
    UnifiedProject,
    UnifiedStatus,
    UnifiedTask,
    UnifiedUser,
)


def monday_user_to_unified(raw: dict[str, Any]) -> UnifiedUser:
    uid = str(raw.get("id") or "")
    return UnifiedUser(
        id=uid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        email=raw.get("email") if isinstance(raw.get("email"), str) else None,
        provider="monday",
        raw={"id": uid},
    )


def monday_board_to_unified(raw: dict[str, Any]) -> UnifiedProject:
    bid = str(raw.get("id") or "")
    state = raw.get("state")
    archived = state == "archived" if isinstance(state, str) else None
    return UnifiedProject(
        id=bid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        provider="monday",
        archived=archived,
        permalink_url=None,
        raw={"id": bid, "state": state, "board_kind": raw.get("board_kind")},
    )


def _status_from_column_values(columns: list[dict[str, Any]] | None) -> UnifiedStatus | None:
    if not columns:
        return None
    for c in columns:
        if not isinstance(c, dict):
            continue
        if str(c.get("type") or "").lower() == "status":
            txt = c.get("text")
            if isinstance(txt, str) and txt.strip():
                return UnifiedStatus(label=txt, resource_type="status", provider="monday")
    for c in columns:
        if isinstance(c, dict):
            t = c.get("text")
            if isinstance(t, str) and t.strip():
                return UnifiedStatus(label=t, resource_type=str(c.get("type")), provider="monday")
    return None


def monday_item_to_unified(raw: dict[str, Any], *, board_id: str) -> UnifiedTask:
    iid = str(raw.get("id") or "")
    cols = raw.get("column_values")
    col_list = cols if isinstance(cols, list) else None
    st = _status_from_column_values([x for x in col_list if isinstance(x, dict)] if col_list else None)
    state = raw.get("state")
    completed = state == "archived" if isinstance(state, str) else None
    return UnifiedTask(
        id=iid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        completed=completed,
        due_on=None,
        due_at=None,
        assignee_user_id=None,
        project_ids=[board_id],
        status=st,
        permalink_url=None,
        provider="monday",
        raw={"id": iid, "state": state, "column_values": col_list or []},
    )


def monday_update_to_activity(raw: dict[str, Any]) -> UnifiedActivity:
    """Map a webhook/update-style payload fragment when present."""
    uid = str(raw.get("id") or raw.get("updateId") or "")
    return UnifiedActivity(
        id=uid or "unknown",
        resource_type="update",
        text=raw.get("textBody") if isinstance(raw.get("textBody"), str) else None,
        created_at=raw.get("triggerTime") if isinstance(raw.get("triggerTime"), str) else None,
        created_by_user_id=str(raw["userId"]) if raw.get("userId") is not None else None,
        provider="monday",
        raw=dict(raw),
    )
