from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models_generated import Domains
from app.schemas import DomainCatalogRow

router = APIRouter(prefix="/api/v1", tags=["catalog", "domains"])


def _dt_iso(v: datetime | None) -> str | None:
    if v is None:
        return None
    return v.isoformat()


@router.get("/domains", response_model=list[DomainCatalogRow])
def list_domains(session: Session = Depends(get_db)) -> list[DomainCatalogRow]:
    """List GRC domain catalog rows (primary label: ``evidence_sources``)."""
    rows = session.scalars(
        select(Domains).order_by(Domains.domain_group, Domains.evidence_sources)
    ).all()
    if not rows:
        return []
    out: list[DomainCatalogRow] = []
    for d in rows:
        out.append(
            DomainCatalogRow(
                id=str(d.id),
                domain_group=d.domain_group,
                evidence_sources=d.evidence_sources,
                primary_evidence=d.primary_evidence,
                secondary_evidence=d.secondary_evidence,
                common_tools=d.common_tools,
                created_at=_dt_iso(d.created_at),
                updated_at=_dt_iso(d.updated_at),
            )
        )
    return out
