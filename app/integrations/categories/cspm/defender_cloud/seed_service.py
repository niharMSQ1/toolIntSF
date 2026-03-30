"""Upsert evidence_masters for Microsoft Defender for Cloud."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.cspm.defender_cloud.constants import DEFENDER_CLOUD_SOURCE
from app.integrations.categories.cspm.defender_cloud.seed import DEFENDER_CSPM_SEED_ROWS
from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.models import EvidenceMaster


def _api_endpoint_for_row(row: dict[str, str]) -> str:
    return (row.get("api_endpoint") or "").strip() or "azure_arm_microsoft_security"


def seed_defender_cloud_evidence_masters(session: Session, tool_id: str) -> int:
    did = get_domain_id_for_tool(session, tool_id)
    now = datetime.now(timezone.utc)
    touched = 0
    for row in DEFENDER_CSPM_SEED_ROWS:
        code = row["code"]
        em = session.scalars(select(EvidenceMaster).where(EvidenceMaster.code == code).limit(1)).first()
        api_endpoint = _api_endpoint_for_row(row)
        if em is None:
            session.add(
                EvidenceMaster(
                    id=uuid.uuid4(),
                    domain_id=did,
                    name=row["name"],
                    code=code,
                    category=row["category"],
                    source=DEFENDER_CLOUD_SOURCE,
                    evidence_type="API",
                    api_endpoint=api_endpoint,
                    description=None,
                    is_required_evidence=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            touched += 1
            continue
        if em.domain_id != did:
            continue
        if (
            em.name != row["name"]
            or em.category != row["category"]
            or (em.source or "") != DEFENDER_CLOUD_SOURCE
            or (em.api_endpoint or "") != api_endpoint
        ):
            em.name = row["name"]
            em.category = row["category"]
            em.source = DEFENDER_CLOUD_SOURCE
            em.api_endpoint = api_endpoint
            em.updated_at = now
            touched += 1
    if touched:
        session.commit()
    else:
        session.rollback()
    return touched
