import datetime
import uuid
from typing import Any, Dict, Iterable

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
    print("[Zoho Employee Directory] response:", employee_data)
    _sync_employees_from_zoho(
        db=db,
        integration=integration,
        employee_payload=employee_data,
    )
    department_data = await zoho_client.fetch_department_structure(access_token)

    # 2) Create evidence rows
    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=10)

    evidence_items: Dict[str, Dict[str, Any]] = {
        "Employee Directory": {
            "tool_payload": employee_data,
            "title": "Zoho Employee Directory",
        },
        "Department Structure": {
            "tool_payload": department_data,
            "title": "Zoho Department Structure",
        },
    }

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
                    existing.status = "active"
                    existing.updated_at = now
                else:
                    employee_row = Employees(
                        id=uuid.uuid4(),
                        organization_id=org_id,
                        email=email,
                        status="active",
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
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(employee_row)


EVIDENCEABLE_TYPE_CONTROL = "App/Models/Control"


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

