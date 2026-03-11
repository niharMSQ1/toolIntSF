import datetime
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import (
    ControlScenarios,
    Evidence,
    EvidenceCollections,
    EvidenceMappeds,
    ToolIntegrations,
)
from .client import JiraServicedeskClient


EVIDENCEABLE_TYPE_CONTROL = "App/Models/Control"


async def collect_and_persist_evidence(
    db: Session,
    integration: ToolIntegrations,
    access_token: str,
) -> None:
    """
    - Get cloud_id from integration config
    - Fetch Service Desks and Customer Requests from JSM
    - Create Evidence rows ("Service Desks", "Customer Requests")
    - Create EvidenceCollections with raw API payloads
    - Map to controls via ControlScenarios -> EvidenceMappeds
    """
    config = integration.configuration_data or {}
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    redirect_uri = config.get("redirect_uri")
    cloud_id = config.get("cloud_id")

    if not cloud_id:
        raise ValueError("cloud_id missing in integration configuration_data")

    jira_client = JiraServicedeskClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    servicedesk_data = await jira_client.fetch_servicedesks(cloud_id, access_token)
    requests_data = await jira_client.fetch_customer_requests(cloud_id, access_token)

    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=10)

    evidence_items = {
        "Service Desks": {
            "tool_payload": servicedesk_data,
            "title": "Jira Service Management - Service Desks",
        },
        "Customer Requests": {
            "tool_payload": requests_data,
            "title": "Jira Service Management - Customer Requests",
        },
    }

    for evidence_name, info in evidence_items.items():
        evidence = Evidence(
            id=uuid.uuid4(),
            organization_id=integration.organization_id,
            tool_id=integration.tool_id,
            title=info["title"],
            description=f"Evidence collected from Jira Service Management - {evidence_name}",
            due_date=due_date,
            status="active",
            created_at=datetime.datetime.utcnow(),
        )
        db.add(evidence)
        db.flush()

        collection = EvidenceCollections(
            id=uuid.uuid4(),
            evidence_id=evidence.id,
            evidence_from="integration",
            source="Jira Service Management",
            name=evidence_name,
            tool_evidence=info["tool_payload"],
            created_at=datetime.datetime.utcnow(),
        )
        db.add(collection)

        _map_evidence_to_controls(
            db=db,
            evidence=evidence,
            tool_id=integration.tool_id,
            evidence_name=evidence_name,
            mapped_by=str(integration.user_id),
        )


def _map_evidence_to_controls(
    db: Session,
    evidence: Evidence,
    tool_id: uuid.UUID,
    evidence_name: str,
    mapped_by: str,
) -> None:
    """
    Find ControlScenarios for this tool_id and evidence_name (case-insensitive).
    For each, upsert EvidenceMappeds (one per evidence_id + evidenceable_id).
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
