"""Seed `evidence_masters` for Bitbucket-backed DevOps evidence (EV-*), when rows are missing.

Call manually when needed (not from POST /configure).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.devtools.bitbucket.constants import BITBUCKET_CLOUD_SOURCE
from app.integrations.categories.devtools.bitbucket.evidence_map import DEVOPS_EVIDENCE_SEED_ROWS
from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.models import EvidenceMaster


def seed_bitbucket_evidence_masters(session: Session, tool_id: str) -> int:
    did = get_domain_id_for_tool(session, tool_id)
    count = 0
    for row in DEVOPS_EVIDENCE_SEED_ROWS:
        # `evidence_masters.code` is globally unique — skip if this code exists anywhere.
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
                source=BITBUCKET_CLOUD_SOURCE,
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
