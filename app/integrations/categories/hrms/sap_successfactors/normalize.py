"""Map SAP SuccessFactors OData entities to ``hrms.common_schema``."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.hrms.common_schema import HREmployee, HREvent


def _pick(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def odata_extract_results(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict):
        d = body.get("d")
        if isinstance(d, dict):
            res = d.get("results")
            if isinstance(res, list):
                return [x for x in res if isinstance(x, dict)]
        val = body.get("value")
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    return []


def sf_user_to_employee(raw: dict[str, Any]) -> HREmployee:
    uid = str(_pick(raw, "userId", "id") or "")
    name = raw.get("displayName") or raw.get("name")
    if isinstance(name, dict):
        name = name.get("formattedName") or name.get("name")
    email = raw.get("email") or raw.get("businessEmail")
    return HREmployee(
        id=uid,
        employee_number=str(raw.get("empId")) if raw.get("empId") is not None else None,
        display_name=str(name) if name else None,
        email=str(email) if email and not isinstance(email, dict) else None,
        phone=None,
        hire_date=None,
        termination_date=None,
        employment_status=str(raw.get("status")) if raw.get("status") is not None else None,
        manager_id=None,
        department_id=None,
        job_title=None,
        provider="sap_successfactors",
        raw=raw,
    )


def sf_webhook_to_event(payload: dict[str, Any]) -> HREvent:
    return HREvent(
        id=None,
        event_type=str(payload.get("type")) if payload.get("type") is not None else None,
        employee_id=str(payload.get("userId")) if payload.get("userId") is not None else None,
        occurred_at=None,
        provider="sap_successfactors",
        raw=payload,
    )
