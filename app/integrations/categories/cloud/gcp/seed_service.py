"""Seed and refresh evidence_masters for GCP (Cloud domain)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.cloud.gcp.constants import GCP_SOURCE
from app.integrations.categories.cloud.gcp.evidence_map import GCP_SEED_ROWS
from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.models import EvidenceMaster


def _api_endpoint_for_row(row: dict[str, str]) -> str:
    return (row.get("api_endpoint") or "").strip() or "gcp_rest_api"


def seed_gcp_evidence_masters(session: Session, tool_id: str) -> int:
    did = get_domain_id_for_tool(session, tool_id)
    now = datetime.now(timezone.utc)
    touched = 0

    for row in GCP_SEED_ROWS:
        code = row["code"]
        name = row["name"]
        category = row["category"]
        api_endpoint = _api_endpoint_for_row(row)

        em = session.scalars(select(EvidenceMaster).where(EvidenceMaster.code == code).limit(1)).first()
        if em is None:
            session.add(
                EvidenceMaster(
                    id=uuid.uuid4(),
                    domain_id=did,
                    name=name,
                    code=code,
                    category=category,
                    source=GCP_SOURCE,
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
            em.name != name
            or em.category != category
            or (em.source or "") != GCP_SOURCE
            or (em.api_endpoint or "") != api_endpoint
        ):
            em.name = name
            em.category = category
            em.source = GCP_SOURCE
            em.api_endpoint = api_endpoint
            em.updated_at = now
            touched += 1

    if touched:
        session.commit()
    else:
        session.rollback()
    return touched

