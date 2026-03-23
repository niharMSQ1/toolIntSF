"""Seed `evidence_masters` rows for Zoho People (per tool_id)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.hrms.zoho_people.seed import ZOHO_EVIDENCE_SEED_ROWS
from app.models import EvidenceMaster


def _uuid(x: str | uuid.UUID) -> uuid.UUID:
    return x if isinstance(x, uuid.UUID) else uuid.UUID(str(x))


def seed_zoho_evidence_masters(session: Session, tool_id: str) -> int:
    tid = _uuid(tool_id)
    count = 0
    for row in ZOHO_EVIDENCE_SEED_ROWS:
        exists = session.scalars(
            select(EvidenceMaster.id).where(
                EvidenceMaster.tool_id == tid,
                EvidenceMaster.code == row["code"],
            ).limit(1)
        ).first()
        if exists:
            continue
        now = datetime.now(timezone.utc)
        session.add(
            EvidenceMaster(
                id=uuid.uuid4(),
                tool_id=tid,
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
