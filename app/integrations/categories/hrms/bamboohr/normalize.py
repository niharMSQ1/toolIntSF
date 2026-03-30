"""BambooHR directory / employee payloads to unified HR schema."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.hrms.common_schema import HREmployee, HREvent


def bamboo_extract_employees(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict):
        emps = body.get("employees")
        if isinstance(emps, list):
            return [x for x in emps if isinstance(x, dict)]
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    return []


def bamboo_row_to_employee(raw: dict[str, Any]) -> HREmployee:
    pid = str(raw.get("id") or raw.get("employeeId") or "")
    dn = raw.get("displayName") or raw.get("preferredName")
    if not dn and (raw.get("firstName") or raw.get("lastName")):
        dn = f"{raw.get('firstName', '')} {raw.get('lastName', '')}".strip()
    return HREmployee(
        id=pid,
        employee_number=str(raw.get("employeeNumber")) if raw.get("employeeNumber") is not None else None,
        display_name=str(dn) if dn else None,
        email=str(raw.get("workEmail")) if isinstance(raw.get("workEmail"), str) else None,
        phone=str(raw.get("workPhone")) if isinstance(raw.get("workPhone"), str) else None,
        hire_date=str(raw.get("hireDate")) if isinstance(raw.get("hireDate"), str) else None,
        termination_date=str(raw.get("terminationDate")) if isinstance(raw.get("terminationDate"), str) else None,
        employment_status=str(raw.get("employmentHistoryStatus")) if raw.get("employmentHistoryStatus") is not None else None,
        manager_id=str(raw.get("supervisorId")) if raw.get("supervisorId") is not None else None,
        department_id=str(raw.get("department")) if raw.get("department") is not None else None,
        job_title=str(raw.get("jobTitle")) if isinstance(raw.get("jobTitle"), str) else None,
        provider="bamboohr",
        raw=raw,
    )


def bamboo_webhook_to_event(payload: dict[str, Any]) -> HREvent:
    return HREvent(
        id=None,
        event_type=str(payload.get("type")) if payload.get("type") is not None else None,
        employee_id=str(payload.get("employeeId")) if payload.get("employeeId") is not None else None,
        occurred_at=None,
        provider="bamboohr",
        raw=payload,
    )
