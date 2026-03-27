"""Seed `evidence_masters` rows for ServiceNow ITSM integrations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.integrations.categories.itsm.servicenow.seed import SERVICENOW_EVIDENCE_SCHEMAS, schema_description
from app.models import EvidenceMaster


def seed_servicenow_evidence_masters(session: Session, tool_id: str) -> int:
    did = get_domain_id_for_tool(session, tool_id)
    count = 0
    for row in SERVICENOW_EVIDENCE_SCHEMAS:
        exists = session.scalars(
            select(EvidenceMaster.id).where(
                EvidenceMaster.code == row["code"],
            ).limit(1)
        ).first()
        if exists:
            continue
        now = datetime.now(timezone.utc)
        session.add(
            EvidenceMaster(
                id=uuid.uuid4(),
                domain_id=did,
                name=row["name"],
                code=row["code"],
                category=row["category"],
                source="servicenow",
                evidence_type="API",
                api_endpoint=row.get("api"),
                description=schema_description(row),
                is_required_evidence=True,
                created_at=now,
                updated_at=now,
            )
        )
        count += 1
    if count:
        session.commit()
    else:
        session.rollback()
    return count
