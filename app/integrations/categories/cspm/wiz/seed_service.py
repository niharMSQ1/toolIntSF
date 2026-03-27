"""Seed evidence_masters for Wiz (CSPM) when codes are not already present globally."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.cspm.wiz.constants import WIZ_SOURCE
from app.integrations.categories.cspm.wiz.seed import CSPM_WIZ_SEED_ROWS
from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.models import EvidenceMaster


def seed_wiz_evidence_masters(session: Session, tool_id: str) -> int:
    did = get_domain_id_for_tool(session, tool_id)
    count = 0
    for row in CSPM_WIZ_SEED_ROWS:
        exists_anywhere = session.scalars(
            select(EvidenceMaster.id).where(EvidenceMaster.code == row["code"]).limit(1)
        ).first()
        if exists_anywhere:
            continue
        now = datetime.now(timezone.utc)
        session.add(
            EvidenceMaster(
                id=uuid.uuid4(),
                domain_id=did,
                name=row["name"],
                code=row["code"],
                category=row["category"],
                source=WIZ_SOURCE,
                evidence_type="API",
                api_endpoint=None,
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
