import datetime
import logging
import uuid
from typing import Any, Dict, Iterable, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import (
    ControlScenarios,
    Evidence,
    EvidenceCollections,
    EvidenceMappeds,
    Employees,
    ToolIntegrations,
)
from .client import ZohoPeopleClient
from .config import ATTENDANCE_ENDPOINT, TRAINING_FORM_LINK_NAME

# Evidence names we consider for Zoho collection. Unsupported names are skipped.
DESIRED_EVIDENCE_NAMES = [
    "Employee Directory",
    "Department Structure",
    "Employee Termination Records",
    "Employee Onboarding Records",
    "Employee Profile Verification",
    "Attendance Records",
    "Training Completion Records",
    "Access Revocation Logs",
    "User Access Permissions",
    "System Audit Logs",
    "User Activity Logs",
    "Role-Based Access Control",
]
EVIDENCE_NAMES_NOT_IN_ZOHO = {
    "Access Revocation Logs",
    "User Access Permissions",
    "System Audit Logs",
    "User Activity Logs",
    "Role-Based Access Control",
}


def _has_exit_date(record: Dict[str, Any]) -> bool:
    """True if the employee record has a non-empty exit/termination date."""
    exit_keys = (
        "LastWorkingDate", "Last Working Date", "Date_of_Exit", "Date of Exit",
        "TerminationDate", "Termination Date", "Relieving Date", "RelievingDate",
        "Dateofexit",
    )
    for key in exit_keys:
        if record.get(key) and str(record.get(key)).strip():
            return True
    for k, v in record.items():
        if v and isinstance(k, str) and isinstance(v, (str, int, float)) and (
            "exit" in k.lower() or "last work" in k.lower()
            or "terminat" in k.lower() or "reliev" in k.lower()
        ):
            if str(v).strip():
                return True
    return False


def _has_join_date(record: Dict[str, Any]) -> bool:
    """True if the employee record has a join/onboarding date."""
    for key in ("Dateofjoining", "Date of Joining", "DateOfJoining", "AddedTime"):
        if record.get(key) and str(record.get(key)).strip():
            return True
    return False


def _filter_employee_response(
    employee_payload: Dict[str, Any],
    predicate: Any,
) -> Dict[str, Any]:
    """
    Filter employee response.result by predicate(record). Returns same shape:
    { "response": { "result": [ ... ], "status": ..., "message": ... } }.
    """
    response = (employee_payload or {}).get("response") or {}
    result: list = list(response.get("result") or [])
    filtered_result: list = []
    for entry in result:
        if not isinstance(entry, dict):
            continue
        for zoho_key, records in entry.items():
            if not isinstance(records, list):
                continue
            for record in records:
                if isinstance(record, dict) and predicate(record):
                    filtered_result.append({zoho_key: [record]})
                    break
            else:
                continue
            break
    return {
        "response": {
            **response,
            "result": filtered_result,
        },
    }


async def collect_and_persist_evidence(
    db: Session,
    integration: ToolIntegrations,
    access_token: str,
) -> None:
    """
    - Collect Employee Directory and Department Structure from Zoho
    - Create Evidence rows for each evidence_name
    - Create EvidenceCollections rows storing the raw tool payloads
    - Map to Controls via ControlScenarios into EvidenceMappeds
    """
    config = integration.configuration_data or {}
    region = config["region"]
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    redirect_uri = config["redirect_uri"]

    zoho_client = ZohoPeopleClient(
        region=region,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    # 1) Call Zoho APIs
    employee_data = await zoho_client.fetch_employee_directory(access_token)




    _sync_employees_from_zoho(
        db=db,
        integration=integration,
        employee_payload=employee_data,
    )
    department_data = await zoho_client.fetch_department_structure(access_token)

    # Derived payloads from employee directory (no extra API calls)
    termination_data = _filter_employee_response(employee_data, _has_exit_date)
    onboarding_data = _filter_employee_response(employee_data, _has_join_date)

    # Build evidence_items only for names we can provide; skip names not in Zoho
    evidence_items: Dict[str, Dict[str, Any]] = {}
    # Always add these (we have data)
    evidence_items["Employee Directory"] = {
        "tool_payload": employee_data,
        "title": "Zoho Employee Directory",
    }
    evidence_items["Department Structure"] = {
        "tool_payload": department_data,
        "title": "Zoho Department Structure",
    }
    evidence_items["Employee Termination Records"] = {
        "tool_payload": termination_data,
        "title": "Zoho Employee Termination Records",
    }
    evidence_items["Employee Onboarding Records"] = {
        "tool_payload": onboarding_data,
        "title": "Zoho Employee Onboarding Records",
    }
    evidence_items["Employee Profile Verification"] = {
        "tool_payload": employee_data,
        "title": "Zoho Employee Profile Verification",
    }

    # Optional: Attendance Records (best-effort; skip on failure)
    if "Attendance Records" not in EVIDENCE_NAMES_NOT_IN_ZOHO:
        try:
            attendance_payload = await zoho_client.fetch_attendance(
                access_token,
                params={"fromDate": (datetime.date.today() - datetime.timedelta(days=30)).isoformat(), "toDate": datetime.date.today().isoformat()},
            )
            evidence_items["Attendance Records"] = {
                "tool_payload": attendance_payload,
                "title": "Zoho Attendance Records",
            }
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).info(
                "Skipping Attendance Records: not available or API error - %s", e
            )

    # Optional: Training Completion Records (only if form name configured)
    if (
        "Training Completion Records" not in EVIDENCE_NAMES_NOT_IN_ZOHO
        and TRAINING_FORM_LINK_NAME
    ):
        try:
            training_payload = await zoho_client.fetch_form_records(
                access_token, TRAINING_FORM_LINK_NAME
            )
            evidence_items["Training Completion Records"] = {
                "tool_payload": training_payload,
                "title": "Zoho Training Completion Records",
            }
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).info(
                "Skipping Training Completion Records: not configured or API error - %s", e
            )

    # Log which desired evidence names are skipped (not provided by Zoho)
    skipped = EVIDENCE_NAMES_NOT_IN_ZOHO
    if skipped:
        logging.getLogger(__name__).debug(
            "Skipping evidence names not provided by Zoho: %s", sorted(skipped)
        )

    # 2) Create evidence rows
    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=10)

    for evidence_name, info in evidence_items.items():
        evidence = Evidence(
            id=uuid.uuid4(),
            organization_id=integration.organization_id,
            tool_id=integration.tool_id,
            title=info["title"],
            description=f"Evidence collected from Zoho People - {evidence_name}",
            due_date=due_date,
            status="active",
            created_at=datetime.datetime.utcnow(),
        )
        db.add(evidence)
        db.flush()  # to get evidence.id without committing yet

        # Evidence collection record
        collection = EvidenceCollections(
            id=uuid.uuid4(),
            evidence_id=evidence.id,
            evidence_from="integration",
            source="Zoho People",
            name=evidence_name,
            tool_evidence=info["tool_payload"],
            created_at=datetime.datetime.utcnow(),
        )
        db.add(collection)

        # 3) Map evidence to controls via ControlScenarios
        _map_evidence_to_controls(
            db=db,
            evidence=evidence,
            tool_id=integration.tool_id,
            evidence_name=evidence_name,
            mapped_by=str(integration.user_id),
        )

    # No commit here — caller commits once after entire flow succeeds.


def _parse_zoho_date(value: Any) -> Optional[datetime.datetime]:
    """
    Parse date from Zoho People API (may be ISO string, MM/DD/YYYY, or timestamp ms).
    Returns datetime in UTC or None if unparseable.
    """
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    if isinstance(value, (int, float)):
        try:
            return datetime.datetime.utcfromtimestamp(value / 1000.0 if value > 1e12 else value)
        except (OSError, ValueError):
            return None
    s = str(value).strip()
    if not s:
        return None
    # Try ISO with timezone first
    if "T" in s and ("+" in s or "Z" in s or "-" in s[10:11]):
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                part = s.replace("Z", "+00:00")[:25]
                dt = datetime.datetime.strptime(part[:19], "%Y-%m-%dT%H:%M:%S")
                return dt
            except ValueError:
                continue
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(s[:10], fmt)
        except ValueError:
            continue
    return None


def _sync_employees_from_zoho(
    db: Session,
    integration: ToolIntegrations,
    employee_payload: Dict[str, Any],
) -> None:
    """
    Upsert employees from Zoho People Employee Directory into Employees table.

    - Uniqueness: (organization_id, email) must be unique (enforced by DB).
    - If an employee with that org/email exists, update basic fields.
    - Otherwise, create a new Employees row.
    """
    org_id = integration.organization_id
    sync_user_id = integration.user_id
    now = datetime.datetime.utcnow()

    # Zoho People employee payload structure:
    # {
    #   "response": {
    #     "result": [
    #       { "325560000000294289": [ { ... employee fields ... } ] },
    #       { "325560000000294287": [ { ... } ] },
    #       ...
    #     ],
    #     "status": 0,
    #     "message": "Data fetched successfully",
    #   }
    # }
    response = (employee_payload or {}).get("response") or {}
    result: Iterable[dict] = response.get("result") or []

    for entry in result:
        if not isinstance(entry, dict):
            continue
        for _zoho_key, records in entry.items():
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue

                email = (record.get("EmailID") or "").strip()
                if not email:
                    continue

                first_name = (record.get("FirstName") or "").strip()
                last_name = (record.get("LastName") or "").strip()
                full_name = (first_name + " " + last_name).strip() or None

                department = (record.get("Department") or "").strip() or None
                designation = (record.get("Designation") or "").strip() or None
                employee_status = (record.get("Employeestatus") or "").strip() or None

                image = (
                    (record.get("Photo_downloadUrl") or "").strip()
                    or (record.get("Photo") or "").strip()
                    or None
                )

                provider = "zoho_people"
                provider_id = str(record.get("Zoho_ID") or record.get("EmployeeID") or "").strip() or None

                # Parse date_of_exit from common Zoho field names (API may use display name or internal ID)
                date_of_exit = None
                for key in (
                    "LastWorkingDate",
                    "Last Working Date",
                    "Date_of_Exit",
                    "Date of Exit",
                    "TerminationDate",
                    "Termination Date",
                    "Relieving Date",
                    "RelievingDate",
                ):
                    if key in record and record[key]:
                        date_of_exit = _parse_zoho_date(record[key])
                        if date_of_exit is not None:
                            break
                if date_of_exit is None:
                    for k, v in record.items():
                        if v and isinstance(k, str) and (
                            "exit" in k.lower() or "last work" in k.lower() or "terminat" in k.lower() or "reliev" in k.lower()
                        ):
                            date_of_exit = _parse_zoho_date(v)
                            if date_of_exit is not None:
                                break

                existing = db.scalars(
                    select(Employees).where(
                        Employees.organization_id == org_id,
                        Employees.email == email,
                    )
                ).first()

                if existing:
                    existing.name = full_name or existing.name
                    existing.department = department or existing.department
                    existing.designation = designation or existing.designation
                    existing.employee_status = employee_status or existing.employee_status
                    existing.image = image or existing.image
                    existing.provider = provider
                    existing.provider_id = provider_id or existing.provider_id
                    existing.sync_user_id = sync_user_id
                    existing.updated_at = now
                    existing.date_of_exit = date_of_exit
                    existing.status = "inactive" if date_of_exit else (existing.status or "active")
                else:
                    employee_row = Employees(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        email=email,
                        status="inactive" if date_of_exit else "active",
                        mode=False,
                        has_changed=False,
                        sync_user_id=sync_user_id,
                        department=department,
                        designation=designation,
                        name=full_name,
                        image=image,
                        provider=provider,
                        provider_id=provider_id,
                        employee_status=employee_status,
                        date_of_exit=date_of_exit,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(employee_row)


EVIDENCEABLE_TYPE_CONTROL = "App\Models\Control"


def _map_evidence_to_controls(
    db: Session,
    evidence: Evidence,
    tool_id: uuid.UUID,
    evidence_name: str,
    mapped_by: str,
) -> None:
    """
    For a given evidence_name and tool_id:
    - Find all ControlScenarios rows (case-insensitive evidence_name match)
    - For each, ensure exactly one EvidenceMappeds row per (evidence_id, evidenceable_id):
      update existing row (mapped_by, updated_at) or insert new one. Keeps evidence_id +
      evidenceable_id unique.
    """
    now = datetime.datetime.utcnow()
    stmt = (
        select(ControlScenarios)
        .where(ControlScenarios.tool_id == tool_id)
        .where(func.lower(ControlScenarios.evidence_name) == evidence_name.lower())
    )
    scenarios = db.scalars(stmt).all()

    for scenario in scenarios:
        existing = db.scalars(
            select(EvidenceMappeds).where(
                EvidenceMappeds.evidence_id == evidence.id,
                EvidenceMappeds.evidenceable_type == EVIDENCEABLE_TYPE_CONTROL,
                EvidenceMappeds.evidenceable_id == scenario.control_id,
            )
        ).first()

        if existing:
            existing.mapped_by = mapped_by
            existing.updated_at = now
        else:
            mapping = EvidenceMappeds(
                id=uuid.uuid4(),
                evidence_id=evidence.id,
                evidenceable_type=EVIDENCEABLE_TYPE_CONTROL,
                evidenceable_id=scenario.control_id,
                mapped_by=mapped_by,
                created_at=now,
                updated_at=now,
            )
            db.add(mapping)

