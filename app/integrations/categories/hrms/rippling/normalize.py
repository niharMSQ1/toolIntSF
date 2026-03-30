"""Rippling API payloads to unified HR schema."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.hrms.common_schema import HREmployee, HREvent


def rippling_extract_employees(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict):
        for key in ("employees", "data", "items", "results"):
            v = body.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    return []


def rippling_row_to_employee(raw: dict[str, Any]) -> HREmployee:
    pid = str(raw.get("id") or raw.get("employeeId") or "")
    name = raw.get("name") or raw.get("fullName") or raw.get("displayName")
    return HREmployee(
        id=pid,
        employee_number=str(raw.get("employeeNumber")) if raw.get("employeeNumber") is not None else None,
        display_name=str(name) if name else None,
        email=str(raw.get("email")) if isinstance(raw.get("email"), str) else None,
        phone=str(raw.get("phone")) if isinstance(raw.get("phone"), str) else None,
        hire_date=str(raw.get("hireDate")) if isinstance(raw.get("hireDate"), str) else None,
        termination_date=str(raw.get("terminationDate")) if isinstance(raw.get("terminationDate"), str) else None,
        employment_status=str(raw.get("employmentStatus")) if raw.get("employmentStatus") is not None else None,
        manager_id=str(raw.get("managerId")) if raw.get("managerId") is not None else None,
        department_id=str(raw.get("departmentId")) if raw.get("departmentId") is not None else None,
        job_title=str(raw.get("jobTitle")) if isinstance(raw.get("jobTitle"), str) else None,
        provider="rippling",
        raw=raw,
    )


def rippling_webhook_to_event(payload: dict[str, Any]) -> HREvent:
    return HREvent(
        id=None,
        event_type=str(payload.get("eventType")) if payload.get("eventType") is not None else None,
        employee_id=str(payload.get("employeeId")) if payload.get("employeeId") is not None else None,
        occurred_at=str(payload.get("timestamp")) if isinstance(payload.get("timestamp"), str) else None,
        provider="rippling",
        raw=payload,
    )
