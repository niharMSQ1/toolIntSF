from __future__ import annotations

from typing import Any

from app.integrations.categories.project_management.common_schema import UnifiedProject, UnifiedTask, UnifiedUser


def ss_user_to_unified(raw: dict[str, Any]) -> UnifiedUser:
    uid = str(raw.get("id") or "")
    fn = raw.get("firstName")
    ln = raw.get("lastName")
    name = None
    if isinstance(fn, str) and isinstance(ln, str):
        name = f"{fn} {ln}".strip() or None
    elif isinstance(fn, str):
        name = fn or None
    return UnifiedUser(
        id=uid,
        name=name,
        email=raw.get("email") if isinstance(raw.get("email"), str) else None,
        provider="smartsheet",
        raw={"id": uid},
    )


def ss_sheet_to_unified(raw: dict[str, Any]) -> UnifiedProject:
    sid = str(raw.get("id") or "")
    return UnifiedProject(
        id=sid,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        provider="smartsheet",
        archived=None,
        permalink_url=raw.get("permalink") if isinstance(raw.get("permalink"), str) else None,
        raw={"id": sid},
    )


def ss_row_to_unified(raw: dict[str, Any], *, sheet_id: str) -> UnifiedTask:
    rid = str(raw.get("id") or "")
    cells = raw.get("cells")
    name = None
    if isinstance(cells, list) and cells:
        c0 = cells[0]
        if isinstance(c0, dict) and isinstance(c0.get("displayValue"), str):
            name = c0["displayValue"]
        elif isinstance(c0, dict) and isinstance(c0.get("value"), str):
            name = c0["value"]
    return UnifiedTask(
        id=rid,
        name=name,
        completed=None,
        due_on=None,
        due_at=None,
        assignee_user_id=None,
        project_ids=[sheet_id],
        status=None,
        permalink_url=None,
        provider="smartsheet",
        raw={"id": rid, "sheetId": sheet_id},
    )
