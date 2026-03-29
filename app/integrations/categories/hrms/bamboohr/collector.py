"""Collect BambooHR employee-directory data for evidence records."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.integrations.categories.hrms.bamboohr import api_client
from app.integrations.categories.hrms.bamboohr.credentials import has_usable_credentials
from app.integrations.categories.hrms.bamboohr.seed import CODE_TO_COLLECTOR


def _directory_rows(payload: Any) -> list[dict[str, Any]]:
    """Normalize BambooHR directory responses into a list of employee dicts."""
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("employees", "results", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _first_non_empty(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        raw = row.get(key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    return None


def _status_value(row: dict[str, Any]) -> str:
    return (_first_non_empty(row, ("status", "employeeStatus", "employmentStatus")) or "").lower()


def _is_active_status(value: str) -> bool:
    if any(token in value for token in ("terminated", "inactive", "offboard", "former")):
        return False
    return True


def _is_terminated_status(value: str) -> bool:
    return any(token in value for token in ("terminated", "inactive", "offboard", "former"))


def _parse_directory_date(value: Any) -> datetime | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def fetch_employee_directory(cfg: dict[str, Any]) -> dict[str, Any]:
    """Fetch BambooHR employee directory once and reuse it for many evidence codes."""
    if not has_usable_credentials(cfg):
        raise ValueError("BambooHR credentials are not ready; configure API key or complete app OAuth first.")

    raw = api_client.list_employees_directory(cfg)
    rows = _directory_rows(raw)
    return {
        "source": "bamboohr",
        "collector_key": "employee_directory",
        "api": "/employees/directory",
        "payload": raw,
        "rows": rows,
        "total_rows": len(rows),
    }


def _slim_org_chart_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": _first_non_empty(row, ("id", "employeeId")),
                "display_name": _first_non_empty(row, ("displayName", "name")),
                "job_title": _first_non_empty(row, ("jobTitle", "designation", "title")),
                "department": _first_non_empty(row, ("department", "departmentName")),
                "manager": _first_non_empty(row, ("supervisor", "manager", "supervisorName")),
                "location": _first_non_empty(row, ("location",)),
            }
        )
    return out


def _slim_role_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": _first_non_empty(row, ("id", "employeeId")),
                "display_name": _first_non_empty(row, ("displayName", "name")),
                "work_email": _first_non_empty(row, ("workEmail", "email")),
                "job_title": _first_non_empty(row, ("jobTitle", "designation", "title")),
                "department": _first_non_empty(row, ("department", "departmentName")),
                "division": _first_non_empty(row, ("division",)),
                "location": _first_non_empty(row, ("location",)),
                "status": _first_non_empty(row, ("status", "employeeStatus", "employmentStatus")),
            }
        )
    return out


def _new_hire_rows(rows: list[dict[str, Any]], date_from: str | None, date_to: str | None) -> list[dict[str, Any]]:
    if date_to:
        end = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        end = datetime.now(timezone.utc)
    if date_from:
        start = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start = end - timedelta(days=90)

    out: list[dict[str, Any]] = []
    for row in rows:
        hire_date = _parse_directory_date(_first_non_empty(row, ("hireDate", "dateOfHire", "startDate")))
        if hire_date is None:
            continue
        if start <= hire_date <= end:
            out.append(row)
    return out


def collect_for_master(
    master: dict[str, Any],
    directory_cache: dict[str, Any],
    *,
    date_from: str | None,
    date_to: str | None,
) -> dict[str, Any]:
    """Return BambooHR evidence content for one evidence master."""
    code = str(master.get("code") or "")
    key = CODE_TO_COLLECTOR.get(code)
    if not key:
        raise ValueError(f"No BambooHR collector registered for evidence_masters.code={code!r}")

    rows = list(directory_cache.get("rows") or [])
    payload = directory_cache.get("payload")

    if key == "employee_master":
        data_rows = rows
    elif key == "active_employees":
        data_rows = [row for row in rows if _is_active_status(_status_value(row))]
    elif key == "terminated_employees":
        data_rows = [row for row in rows if _is_terminated_status(_status_value(row))]
    elif key == "org_chart":
        data_rows = _slim_org_chart_rows(rows)
    elif key == "reporting_hierarchy":
        data_rows = _slim_org_chart_rows(rows)
    elif key == "new_hires":
        data_rows = _new_hire_rows(rows, date_from, date_to)
    else:
        data_rows = _slim_role_rows(rows)

    return {
        "source": "bamboohr",
        "collector_key": key,
        "date_from": date_from,
        "date_to": date_to,
        "directory_total_rows": int(directory_cache.get("total_rows") or len(rows)),
        "total_rows": len(data_rows),
        "rows": data_rows,
        "payload": payload,
    }


_BAMBOOHR_STORE_DROP_KEYS: frozenset[str] = frozenset(
    {"source", "collector_key", "date_from", "date_to", "directory_total_rows", "total_rows"}
)


def bamboohr_evidence_for_tool_storage(content: dict[str, Any]) -> Any:
    """Persist BambooHR payload with metadata stripped down to data-bearing fields."""
    return {k: v for k, v in content.items() if k not in _BAMBOOHR_STORE_DROP_KEYS}

