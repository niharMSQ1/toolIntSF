"""Map Workday REST JSON into ``hrms.common_schema`` models (best-effort; WIDs vary by tenant)."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.hrms.common_schema import HRDepartment, HREmployee, HREvent


def extract_item_list(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    if isinstance(body, dict):
        for key in ("data", "Data", "workers", "Workers", "organizations", "Organizations"):
            v = body.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []


def _str_id(raw: dict[str, Any]) -> str:
    for k in ("id", "workerID", "workerId", "wid"):
        v = raw.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    d = raw.get("descriptor")
    if isinstance(d, str) and d.strip():
        return d.strip()
    return ""


def workday_worker_to_employee(raw: dict[str, Any]) -> HREmployee:
    wid = _str_id(raw)
    name = raw.get("descriptor") if isinstance(raw.get("descriptor"), str) else None
    email = None
    phone = None
    hire = None
    term = None
    status = None
    mgr = None
    dept = None
    title = None
    emp_num = None

    pi = raw.get("personInformation") if isinstance(raw.get("personInformation"), dict) else {}
    if pi:
        email = pi.get("email")
        if isinstance(email, dict):
            email = email.get("emailAddress") or email.get("uri")
        elif not isinstance(email, str):
            ea = pi.get("emailAddress")
            if isinstance(ea, dict):
                email = ea.get("emailAddress")
            elif isinstance(ea, str):
                email = ea
        phone = pi.get("phone") if isinstance(pi.get("phone"), str) else None

    emp = raw.get("employmentInformation") if isinstance(raw.get("employmentInformation"), dict) else {}
    if emp:
        hire = emp.get("hireDate") if isinstance(emp.get("hireDate"), str) else None
        term = emp.get("terminationDate") if isinstance(emp.get("terminationDate"), str) else None
        status = emp.get("workerStatus") if isinstance(emp.get("workerStatus"), str) else None
        jref = emp.get("jobProfile") if isinstance(emp.get("jobProfile"), dict) else {}
        if isinstance(jref, dict):
            title = jref.get("descriptor") if isinstance(jref.get("descriptor"), str) else None
        pos = emp.get("position") if isinstance(emp.get("position"), dict) else {}
        if isinstance(pos, dict):
            title = title or (pos.get("jobTitle") if isinstance(pos.get("jobTitle"), str) else None)
        m = emp.get("manager") if isinstance(emp.get("manager"), dict) else {}
        if isinstance(m, dict):
            mgr = _str_id(m) or (m.get("id") if m.get("id") is not None else None)
        d = emp.get("supervisoryOrganization") if isinstance(emp.get("supervisoryOrganization"), dict) else {}
        if isinstance(d, dict):
            dept = str(d.get("id")) if d.get("id") is not None else None

    wo = raw.get("worker") if isinstance(raw.get("worker"), dict) else {}
    if isinstance(wo, dict) and not emp_num:
        emp_num = wo.get("employeeID") if isinstance(wo.get("employeeID"), str) else None

    return HREmployee(
        id=wid,
        employee_number=emp_num,
        display_name=name,
        email=str(email) if email and not isinstance(email, dict) else None,
        phone=phone,
        hire_date=hire,
        termination_date=term,
        employment_status=status,
        manager_id=mgr,
        department_id=dept,
        job_title=title,
        provider="workday",
        raw=raw,
    )


def workday_org_to_department(raw: dict[str, Any]) -> HRDepartment:
    oid = _str_id(raw) or raw.get("organizationID") or ""
    name = raw.get("descriptor") if isinstance(raw.get("descriptor"), str) else raw.get("name")
    code = raw.get("organizationCode") if isinstance(raw.get("organizationCode"), str) else None
    parent = raw.get("parentOrganization") if isinstance(raw.get("parentOrganization"), dict) else {}
    pid = str(parent.get("id")) if isinstance(parent, dict) and parent.get("id") is not None else None
    return HRDepartment(
        id=str(oid),
        name=str(name) if name else None,
        code=code,
        parent_id=pid,
        provider="workday",
        raw=raw,
    )


def workday_webhook_to_event(payload: dict[str, Any]) -> HREvent:
    return HREvent(
        id=None,
        event_type=payload.get("eventType") if isinstance(payload.get("eventType"), str) else None,
        employee_id=str(payload.get("workerId")) if payload.get("workerId") is not None else None,
        occurred_at=payload.get("timestamp") if isinstance(payload.get("timestamp"), str) else None,
        provider="workday",
        raw=payload,
    )
