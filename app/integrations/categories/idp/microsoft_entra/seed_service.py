"""Seed `evidence_masters` rows for Microsoft Entra (per tool domain and cloud)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud
from app.integrations.categories.idp.microsoft_entra.seed import ENTRA_EVIDENCE_SEED_ROWS
from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.models import EvidenceMaster


def evidence_source_for_cloud(cloud: NationalCloud) -> str:
    return "microsoft_entra_gcc_high" if cloud == NationalCloud.GCC_HIGH else "microsoft_entra"


def seed_entra_evidence_masters(session: Session, tool_id: str, *, cloud: NationalCloud) -> int:
    did = get_domain_id_for_tool(session, tool_id)
    source = evidence_source_for_cloud(cloud)
    count = 0
    for row in ENTRA_EVIDENCE_SEED_ROWS:
        exists = session.scalars(
            select(EvidenceMaster.id).where(
                EvidenceMaster.domain_id == did,
                EvidenceMaster.code == row["code"],
                EvidenceMaster.source == source,
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
                source=source,
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
