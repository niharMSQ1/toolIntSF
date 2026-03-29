"""Seed evidence_masters rows for BambooHR."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.hrms.bamboohr.seed import BAMBOOHR_EVIDENCE_SEED_ROWS
from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.models import EvidenceMaster


def seed_bamboohr_evidence_masters(session: Session, tool_id: str) -> int:
    """Insert BambooHR evidence masters for the tool domain if they do not exist yet."""
    did = get_domain_id_for_tool(session, tool_id)
    count = 0
    for row in BAMBOOHR_EVIDENCE_SEED_ROWS:
        exists = session.scalars(
            select(EvidenceMaster.id).where(
                EvidenceMaster.domain_id == did,
                EvidenceMaster.code == row["code"],
                EvidenceMaster.source == "bamboohr",
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
                source="bamboohr",
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

