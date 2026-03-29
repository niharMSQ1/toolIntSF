"""Seed and refresh evidence_masters for AWS (Cloud / Infrastructure).

``evidence_masters.code`` is globally unique (see ``EvidenceMasters`` / ``evidence_masters_code_unique``).
Upsert semantics: insert when the code is missing; when the code exists and ``domain_id`` matches this
tool's Cloud domain, update name/category/source/api_endpoint so deployments stay aligned with code.
If the same code exists for another domain, the row is left unchanged (manual resolution required).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.cloud.aws.constants import AWS_SOURCE
from app.integrations.categories.cloud.aws.seed import AWS_SEED_ROWS
from app.integrations.core.persistence.tool_integration_service import get_domain_id_for_tool
from app.models import EvidenceMaster


def _api_endpoint_for_row(row: dict[str, str]) -> str:
    return (row.get("api_endpoint") or "").strip() or "aws_boto3"


def seed_aws_evidence_masters(session: Session, tool_id: str) -> int:
    """
    Upsert AWS Cloud evidence rows for ``tool_id``'s domain.

    Returns the number of rows inserted or updated (not no-ops skipped due to foreign domain).
    """
    did = get_domain_id_for_tool(session, tool_id)
    now = datetime.now(timezone.utc)
    touched = 0

    for row in AWS_SEED_ROWS:
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
                    source=AWS_SOURCE,
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
            or (em.source or "") != AWS_SOURCE
            or (em.api_endpoint or "") != api_endpoint
        ):
            em.name = name
            em.category = category
            em.source = AWS_SOURCE
            em.api_endpoint = api_endpoint
            em.updated_at = now
            touched += 1

    if touched:
        session.commit()
    else:
        session.rollback()
    return touched
