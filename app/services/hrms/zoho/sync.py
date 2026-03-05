"""
Sync evidence from Zoho People: fetch via API, normalize to 5 HR evidence types, optionally record to DB.
Also sync a flattened view of employees into the employees table (config-less core mapping).
When an existing employee record is updated, has_changed is set to True and the change is appended to changed_values.
"""

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from .client import ZohoPeopleClient, ZohoPeopleClientError
from .normalizer import normalize_zoho_to_hr_payloads

# All personal/synced fields: any change to these is recorded in has_changed and changed_values.
# Add new Zoho-mapped Employee attributes here so they are synced and change-tracked.
_SYNCED_FIELDS = ("email", "name", "department", "designation", "employee_status", "status")

# employees.status has a DB check constraint; only these values are allowed.
_ALLOWED_EMPLOYEE_STATUS = frozenset({"active", "invited", "inactive"})


def _to_allowed_status(zoho_status: str | None) -> str:
    """Map Zoho status (e.g. 'Active') to allowed employees.status value for DB constraint."""
    if not zoho_status or not str(zoho_status).strip():
        return "active"
    s = str(zoho_status).strip().lower()
    return s if s in _ALLOWED_EMPLOYEE_STATUS else "active"


def _normalize_for_compare(val):
    """Treat None and empty string as equal for change detection."""
    if val is None or val == "":
        return None
    if isinstance(val, str):
        val = val.strip()
        return val if val else None
    return val


def _parse_changed_values(raw: str | None) -> list[dict]:
    """Parse changed_values JSON; return list of change entries (append-safe)."""
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _sync_employees_to_db(
    *,
    db_session: Session,
    organization_id: UUID,
    employees: list[dict],
) -> None:
    """
    Best-effort mapping of Zoho employees into the employees table.
    Uses core fields that are stable across orgs; keeps logic generic.
    On update: sets has_changed=True and appends { changed_at, old_values, new_values } to changed_values.
    sync_user_id is left null for new employees.
    """
    from app.models import Employee

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    for row in employees or []:
        email = row.get("email") or row.get("EmailID")
        if not email:
            continue

        name = row.get("name") or f"{row.get('FirstName', '')} {row.get('LastName', '')}".strip()
        department = row.get("department_name") or row.get("Department")
        designation = row.get("Designation")
        # Zoho employment status -> employee_status (raw); employees.status must satisfy DB check (e.g. lowercase)
        zoho_status = row.get("status") or row.get("Employeestatus") or "active"
        app_status = _to_allowed_status(zoho_status)
        # provider = tool name (e.g. "zoho_people"), provider_id = tool id (e.g. Zoho record id)
        tool_name = "zoho_people"
        tool_id = str(row.get("id") or row.get("Zoho_ID") or "")

        # All personal values we sync from Zoho; any change is recorded in has_changed / changed_values
        new_values = {
            "email": email,
            "name": name,
            "department": department,
            "designation": designation,
            "employee_status": zoho_status,
            "status": app_status,
        }

        # Prefer match by Zoho employee id (provider_id) so we update the same person when email changes
        existing = None
        if tool_id:
            existing = (
                db_session.query(Employee)
                .filter(
                    Employee.organization_id == organization_id,
                    Employee.provider_id == tool_id,
                    Employee.provider == "zoho_people",
                )
                .first()
            )
        if existing is None:
            existing = (
                db_session.query(Employee)
                .filter(
                    Employee.organization_id == organization_id,
                    Employee.email == email,
                    Employee.provider == "zoho_people",
                )
                .first()
            )

        if existing:
            old_values = {f: getattr(existing, f, None) for f in _SYNCED_FIELDS}
            changed_keys = [
                k for k in _SYNCED_FIELDS
                if _normalize_for_compare(old_values.get(k)) != _normalize_for_compare(new_values.get(k))
            ]
            if changed_keys:
                existing.has_changed = True
                change_entry = {
                    "changed_at": now_iso,
                    "old_values": {k: old_values.get(k) for k in changed_keys},
                    "new_values": {k: new_values.get(k) for k in changed_keys},
                }
                history = _parse_changed_values(existing.changed_values)
                history.append(change_entry)
                existing.changed_values = json.dumps(history)

            for f in _SYNCED_FIELDS:
                setattr(existing, f, new_values.get(f))
            # Always set status to DB-allowed value (constraint employees_status_check)
            existing.status = app_status
            existing.updated_at = now
        else:
            emp = Employee(
                id=uuid4(),
                organization_id=organization_id,
                sync_user_id=None,
                department=department,
                designation=designation,
                name=name,
                email=email,
                password=None,
                image=None,
                provider=tool_name,
                provider_id=tool_id,
                status="active",
                reg_status=None,
                mode=True,
                employee_status=zoho_status,
                remember_token=None,
                created_at=now,
                updated_at=now,
            )
            db_session.add(emp)

    db_session.commit()


def sync_zoho_evidence(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    region: str = "com",
    *,
    record_organization_id: UUID | None = None,
    record_tool_id: UUID | None = None,
    record_to_db: bool = False,
    db_session=None,
) -> dict:
    """
    Fetch employees (and departments if available) from Zoho People, normalize to the 5 HR
    evidence payloads. If record_to_db is True and record_organization_id + record_tool_id
    are set, also persist via EvidenceService and sync employees into employees table.

    Returns:
        {
          "payloads": { evidence_type_code: payload, ... },
          "recorded": bool,
          "error": str | None,
        }
    """
    result: dict = {"payloads": {}, "recorded": False, "error": None}
    try:
        client = ZohoPeopleClient(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            region=region,
        )
        employees = client.fetch_employee_records()
        departments = client.fetch_department_records()
        collected_at = datetime.utcnow()

        payloads = normalize_zoho_to_hr_payloads(
            employees=employees,
            departments=departments if departments else None,
            onboarding_records=None,
            termination_records=None,
            training_completions=None,
            collected_at=collected_at,
        )
        result["payloads"] = payloads

        if record_to_db and db_session and record_organization_id and record_tool_id:
            from app.services.evidence_service import EvidenceService

            svc = EvidenceService(db_session)
            for code, payload in payloads.items():
                svc.record_hr_evidence(
                    organization_id=record_organization_id,
                    tool_id=record_tool_id,
                    evidence_type_code=code,
                    payload=payload,
                    source="zoho_people",
                )

            # Also sync employees table with the fetched employees
            _sync_employees_to_db(
                db_session=db_session,
                organization_id=record_organization_id,
                employees=employees,
            )

            result["recorded"] = True
    except ZohoPeopleClientError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    return result
