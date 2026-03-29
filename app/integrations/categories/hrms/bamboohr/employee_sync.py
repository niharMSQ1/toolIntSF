"""Upsert BambooHR employee directory rows into ``employees``."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Employees

logger = logging.getLogger(__name__)

PROVIDER_BAMBOOHR = "bamboohr"


def _uuid(s: str | uuid.UUID) -> uuid.UUID:
    return s if isinstance(s, uuid.UUID) else uuid.UUID(str(s))


def _truncate(val: str | None, max_len: int) -> str | None:
    if val is None:
        return None
    v = str(val).strip()
    if not v:
        return None
    return v if len(v) <= max_len else v[:max_len]


def _parse_datetime(value: Any) -> datetime | None:
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


def _first_non_empty(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        raw = row.get(key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    return None


def _row_to_employee_fields(row: dict[str, Any]) -> dict[str, Any] | None:
    email = _first_non_empty(row, ("workEmail", "email"))
    if not email:
        return None

    display_name = _first_non_empty(row, ("displayName", "name"))
    employee_id = _first_non_empty(row, ("employeeId", "employeeNumber"))
    provider_id = _first_non_empty(row, ("id", "employeeId"))
    return {
        "email": _truncate(email, 255) or email[:255],
        "name": _truncate(display_name or email, 255),
        "employee_id": _truncate(employee_id, 255),
        "provider_id": _truncate(provider_id, 255),
        "employee_status": _truncate(_first_non_empty(row, ("status", "employeeStatus", "employmentStatus")), 255),
        "department": _truncate(_first_non_empty(row, ("department", "departmentName")), 255),
        "designation": _truncate(_first_non_empty(row, ("jobTitle", "designation", "title")), 255),
        "phone": _truncate(_first_non_empty(row, ("workPhone", "mobilePhone", "phoneNumber")), 255),
        "date_of_joining": _parse_datetime(_first_non_empty(row, ("hireDate", "dateOfHire", "startDate"))),
        "date_of_exit": _parse_datetime(_first_non_empty(row, ("terminationDate", "endDate"))),
        "date_of_birth": _parse_datetime(_first_non_empty(row, ("dateOfBirth", "birthDate"))),
    }


def sync_employees_from_bamboohr(
    session: Session,
    *,
    organization_id: str,
    sync_user_id: str,
    rows: list[dict[str, Any]],
) -> tuple[int, int]:
    """Upsert BambooHR directory rows into the internal employees table."""
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
        if fields is None or not fields["email"]:
            skipped_no_email += 1
            continue

        existing = session.scalars(
            select(Employees).where(Employees.organization_id == oid, Employees.email == fields["email"]).limit(1)
        ).first()

        if existing:
            existing.name = fields["name"] or existing.name
            existing.employee_id = fields["employee_id"] or existing.employee_id
            existing.employee_status = fields["employee_status"] or existing.employee_status
            existing.department = fields["department"] or existing.department
            existing.designation = fields["designation"] or existing.designation
            existing.phone = fields["phone"] or existing.phone
            existing.provider = PROVIDER_BAMBOOHR
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
                    email=fields["email"],
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
                    provider=PROVIDER_BAMBOOHR,
                    provider_id=fields["provider_id"],
                    last_synced_at=now.isoformat(),
                    created_at=now,
                    updated_at=now,
                )
            )
            inserted += 1

    if skipped_no_email:
        logger.warning(
            "BambooHR employee sync: skipped %s row(s) with no email (org=%s)",
            skipped_no_email,
            organization_id,
        )

    session.commit()
    return inserted, updated

