"""Upsert Zoho People employee form rows into ``employees`` (org directory)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Employees

logger = logging.getLogger(__name__)

PROVIDER_ZOHO = "zoho_people"


def _uuid(s: str | uuid.UUID) -> uuid.UUID:
    return s if isinstance(s, uuid.UUID) else uuid.UUID(str(s))


def _truncate(val: str | None, max_len: int) -> str | None:
    if val is None:
        return None
    v = str(val).strip()
    if not v:
        return None
    return v if len(v) <= max_len else v[:max_len]


def _department_str(row: dict[str, Any]) -> str | None:
    raw = row.get("Department") or row.get("Department.name")
    if raw is None:
        return None
    if isinstance(raw, dict):
        return _truncate(str(raw.get("name") or raw.get("zoho_id") or ""), 255)
    return _truncate(str(raw), 255)


def _designation_str(row: dict[str, Any]) -> str | None:
    raw = row.get("Designation") or row.get("Designation.name")
    if raw is None:
        return None
    if isinstance(raw, dict):
        return _truncate(str(raw.get("name") or ""), 255)
    return _truncate(str(raw), 255)


def _employee_status_str(row: dict[str, Any]) -> str | None:
    for k in ("Employeestatus", "Employee status", "employeestatus", "EmployeeStatus"):
        v = row.get(k)
        if v is not None and str(v).strip():
            return _truncate(str(v).strip(), 255)
    for key in row:
        if "status" in key.lower() and "employee" in key.lower():
            v = row.get(key)
            if v is not None and str(v).strip():
                return _truncate(str(v).strip(), 255)
    return None


def _parse_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _row_to_employee_fields(row: dict[str, Any]) -> dict[str, Any] | None:
    email = (row.get("EmailID") or row.get("Email") or "").strip()
    if not email:
        return None
    first = str(row.get("FirstName") or "").strip()
    last = str(row.get("LastName") or "").strip()
    name = _truncate(f"{first} {last}".strip(), 255) or _truncate(email, 255)
    zid = row.get("Zoho_ID")
    provider_id = str(zid).strip() if zid is not None else None
    phone = _truncate(
        str(row.get("Mobile") or row.get("Work_phone") or row.get("Phone") or "") or None,
        255,
    )
    return {
        "email": _truncate(email, 255) or email[:255],
        "name": name,
        "employee_id": _truncate(str(row.get("EmployeeID") or "").strip() or None, 255),
        "provider_id": _truncate(provider_id, 255) if provider_id else None,
        "employee_status": _employee_status_str(row),
        "department": _department_str(row),
        "designation": _designation_str(row),
        "phone": phone,
        "date_of_joining": _parse_datetime(row.get("Dateofjoining") or row.get("Date_of_joining")),
        "date_of_exit": _parse_datetime(row.get("Dateofexit") or row.get("Date_of_exit")),
        "date_of_birth": _parse_datetime(row.get("Dateofbirth") or row.get("Date_of_birth")),
    }


def sync_employees_from_zoho_people(
    session: Session,
    *,
    organization_id: str,
    sync_user_id: str,
    rows: list[dict[str, Any]],
) -> tuple[int, int]:
    """
    Upsert rows from Zoho ``/api/forms/employee/getRecords`` into ``employees``.

    Match on ``(organization_id, email)``. Sets ``provider`` = ``zoho_people`` and
    ``provider_id`` = Zoho ``Zoho_ID`` when present.

    Returns ``(inserted_count, updated_count)``.
    """
    oid = _uuid(organization_id)
    uid = _uuid(sync_user_id)
    now = datetime.now(timezone.utc)
    inserted = 0
    updated = 0
    skipped_no_email = 0

    for row in rows:
        if not isinstance(row, dict):
            continue
        fields = _row_to_employee_fields(row)
        if fields is None:
            skipped_no_email += 1
            continue
        email = fields["email"]
        if not email:
            skipped_no_email += 1
            continue

        existing = session.scalars(
            select(Employees).where(Employees.organization_id == oid, Employees.email == email).limit(1)
        ).first()

        if existing:
            existing.name = fields["name"] or existing.name
            existing.employee_id = fields["employee_id"] or existing.employee_id
            existing.employee_status = fields["employee_status"] or existing.employee_status
            existing.department = fields["department"] or existing.department
            existing.designation = fields["designation"] or existing.designation
            existing.phone = fields["phone"] or existing.phone
            existing.provider = PROVIDER_ZOHO
            if fields["provider_id"]:
                existing.provider_id = fields["provider_id"]
            if fields["date_of_joining"]:
                existing.date_of_joining = fields["date_of_joining"]
            if fields["date_of_exit"]:
                existing.date_of_exit = fields["date_of_exit"]
            if fields["date_of_birth"]:
                existing.date_of_birth = fields["date_of_birth"]
            existing.sync_user_id = uid
            existing.last_synced_at = now.isoformat()
            existing.updated_at = now
            updated += 1
        else:
            session.add(
                Employees(
                    id=uuid.uuid4(),
                    organization_id=oid,
                    email=email,
                    has_changed=False,
                    sync_user_id=uid,
                    name=fields["name"],
                    employee_id=fields["employee_id"],
                    employee_status=fields["employee_status"],
                    employee_type=None,
                    department=fields["department"],
                    designation=fields["designation"],
                    phone=fields["phone"],
                    date_of_joining=fields["date_of_joining"],
                    date_of_exit=fields["date_of_exit"],
                    date_of_birth=fields["date_of_birth"],
                    provider=PROVIDER_ZOHO,
                    provider_id=fields["provider_id"],
                    last_synced_at=now.isoformat(),
                    created_at=now,
                    updated_at=now,
                )
            )
            inserted += 1

    if skipped_no_email:
        logger.warning(
            "Zoho employee sync: skipped %s row(s) with no email (org=%s)",
            skipped_no_email,
            organization_id,
        )

    session.commit()
    return inserted, updated
