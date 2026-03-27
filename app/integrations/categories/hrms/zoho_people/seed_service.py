"""Seed `evidence_masters` rows for Zoho People (scoped by tool domain).

Call manually when needed (not from POST /configure).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.hrms.zoho_people.seed import ZOHO_EVIDENCE_SEED_ROWS
from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.models import EvidenceMaster


def seed_zoho_evidence_masters(session: Session, tool_id: str) -> int:
    did = get_domain_id_for_tool(session, tool_id)
    count = 0
    for row in ZOHO_EVIDENCE_SEED_ROWS:
        exists = session.scalars(
            select(EvidenceMaster.id).where(
                EvidenceMaster.domain_id == did,
                EvidenceMaster.code == row["code"],
                EvidenceMaster.source == "zoho_people",
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
                source="zoho_people",
                evidence_type="API",
                api_endpoint=row.get("api"),
                description=None,
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
