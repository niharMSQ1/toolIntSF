"""Map ADP worker payloads to ``hrms.common_schema``."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.hrms.common_schema import HREmployee, HREvent


def adp_extract_workers(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict):
        for key in ("workers", "Workers", "individuals", "data"):
            v = body.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    return []


def adp_worker_to_employee(raw: dict[str, Any]) -> HREmployee:
    wid = str(raw.get("associateOID") or raw.get("workerID") or raw.get("id") or "")
    name = raw.get("personName") if isinstance(raw.get("personName"), dict) else {}
    display = None
    if isinstance(name, dict):
        display = name.get("formattedName") or name.get("givenName")
    return HREmployee(
        id=wid,
        employee_number=str(raw.get("workerID")) if raw.get("workerID") is not None else None,
        display_name=str(display) if display else None,
        email=None,
        phone=None,
        hire_date=None,
        termination_date=None,
        employment_status=str(raw.get("workerStatusCode")) if raw.get("workerStatusCode") is not None else None,
        manager_id=None,
        department_id=None,
        job_title=None,
        provider="adp",
        raw=raw,
    )


def adp_webhook_to_event(payload: dict[str, Any]) -> HREvent:
    return HREvent(
        id=None,
        event_type=str(payload.get("eventName")) if payload.get("eventName") is not None else None,
        employee_id=str(payload.get("associateOID")) if payload.get("associateOID") is not None else None,
        occurred_at=None,
        provider="adp",
        raw=payload,
    )
