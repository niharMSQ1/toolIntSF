"""
Generic GRC persistence: tool_integrations, evidence, evidence_masters, evidence_collections, mappings.

Platform-specific OAuth and seed data live under `app.integrations.categories.*` (e.g. HRMS Zoho People).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.integrations.core.constants import CONTROL_EVIDENCEABLE_TYPE, EVIDENCE_FROM_TOOL
from app.models import (
    ControlEvidenceMaster,
    Evidence,
    EvidenceCollection,
    EvidenceMapped,
    EvidenceMaster,
    ToolIntegration,
)


def _uuid(x: str | uuid.UUID) -> uuid.UUID:
    return x if isinstance(x, uuid.UUID) else uuid.UUID(str(x))


def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[:max_len]


def _integration_row(t: ToolIntegration) -> dict[str, Any]:
    cfg = t.configuration_data
    if isinstance(cfg, dict):
        out_cfg = dict(cfg)
    elif cfg is None:
        out_cfg = {}
    else:
        raise TypeError("configuration_data must be JSON object from DB")
    return {
        "id": t.id,
        "organization_id": t.organization_id,
        "tool_id": t.tool_id,
        "user_id": t.user_id,
        "configuration_data": out_cfg,
    }


def _master_to_dict(m: EvidenceMaster) -> dict[str, Any]:
    return {
        "id": m.id,
        "tool_id": m.tool_id,
        "name": m.name,
        "code": m.code,
        "category": m.category,
        "source": m.source,
        "evidence_type": m.evidence_type,
        "api_endpoint": m.api_endpoint,
        "description": m.description,
    }


def normalize_evidence_master_description(master: dict[str, Any]) -> str | None:
    """Match `evidence.description` to `evidence_masters.description` (nullable, strip whitespace)."""
    raw = master.get("description")
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def _evidence_to_dict(e: Evidence) -> dict[str, Any]:
    return {
        "id": e.id,
        "organization_id": e.organization_id,
        "title": e.title,
        "code": e.code,
        "description": e.description,
        "status": e.status,
        "tool_id": e.tool_id,
    }


def get_integration(session: Session, org_id: str, tool_id: str) -> dict[str, Any] | None:
    oid, tid = _uuid(org_id), _uuid(tool_id)
    row = session.scalars(
        select(ToolIntegration)
        .where(ToolIntegration.organization_id == oid, ToolIntegration.tool_id == tid)
        .order_by(ToolIntegration.id)
        .limit(1)
    ).first()
    if not row:
        return None
    return _integration_row(row)


def upsert_tool_integration(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    user_id: str,
    configuration_data: dict[str, Any],
) -> dict[str, Any]:
    cfg = dict(configuration_data)
    user_id_col = _uuid(user_id)
    oid, tid = _uuid(org_id), _uuid(tool_id)

    existing = session.scalars(
        select(ToolIntegration)
        .where(ToolIntegration.organization_id == oid, ToolIntegration.tool_id == tid)
        .order_by(ToolIntegration.id)
        .limit(1)
    ).first()
    if existing:
        existing.configuration_data = cfg
        existing.user_id = user_id_col
        existing.is_active = True
        t = existing
    else:
        t = ToolIntegration(
            id=uuid.uuid4(),
            organization_id=oid,
            tool_id=tid,
            user_id=user_id_col,
            configuration_data=cfg,
            is_active=True,
        )
        session.add(t)
    session.commit()
    session.refresh(t)
    cfg_out = t.configuration_data
    return {
        "id": t.id,
        "organization_id": t.organization_id,
        "tool_id": t.tool_id,
        "configuration_data": dict(cfg_out) if isinstance(cfg_out, dict) else {},
    }


def remap_evidence_to_controls(
    session: Session,
    *,
    evidence_id: str | uuid.UUID,
    evidence_master_id: str | uuid.UUID,
) -> int:
    eid = _uuid(evidence_id)
    emid = _uuid(evidence_master_id)
    session.execute(delete(EvidenceMapped).where(EvidenceMapped.evidence_id == eid))
    control_ids = session.scalars(
        select(ControlEvidenceMaster.control_id).where(
            ControlEvidenceMaster.evidence_master_id == emid
        )
    ).all()
    n = 0
    for control_id in control_ids:
        session.add(
            EvidenceMapped(
                id=uuid.uuid4(),
                evidence_id=eid,
                evidenceable_type=CONTROL_EVIDENCEABLE_TYPE,
                evidenceable_id=control_id,
            )
        )
        n += 1
    session.commit()
    return n


def upsert_evidence_full_replace(
    session: Session,
    *,
    organization_id: str,
    title: str,
    tool_id: str,
    evidence_code: str,
    evidence_description: str | None,
) -> dict[str, Any]:
    """
    Persist collected evidence. ``description`` mirrors ``evidence_masters.description``;
    raw API payloads belong in ``evidence_collections.tool_evidence`` (see collection runner).
    """
    status_val = "collected"
    oid = _uuid(organization_id)
    tid_tool = _uuid(tool_id)
    title_db = _truncate(title, 255)
    code_db = _truncate(evidence_code, 255)

    existing = session.scalars(
        select(Evidence).where(Evidence.organization_id == oid, Evidence.title == title_db).limit(1)
    ).first()
    now = datetime.now(timezone.utc)
    if existing:
        existing.code = code_db
        existing.description = evidence_description
        existing.status = status_val
        existing.tool_id = tid_tool
        existing.updated_at = now
        ev = existing
    else:
        ev = Evidence(
            id=uuid.uuid4(),
            organization_id=oid,
            title=title_db,
            code=code_db,
            description=evidence_description,
            due_date=None,
            status=status_val,
            tool_id=tid_tool,
            created_at=now,
            updated_at=now,
        )
        session.add(ev)
    session.commit()
    session.refresh(ev)
    return _evidence_to_dict(ev)


def list_evidence_masters(
    session: Session,
    *,
    tool_id: str,
    evidence_codes: list[str] | None,
    master_name_order: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """
    List evidence_masters for a tool. If ``master_name_order`` is set (e.g. Zoho G3→G4 order),
    rows are sorted by that name sequence; otherwise SQL ``ORDER BY code`` order is kept.
    """
    tid = _uuid(tool_id)
    if evidence_codes:
        stmt = (
            select(EvidenceMaster)
            .where(EvidenceMaster.tool_id == tid, EvidenceMaster.code.in_(evidence_codes))
            .order_by(EvidenceMaster.code)
        )
    else:
        stmt = select(EvidenceMaster).where(EvidenceMaster.tool_id == tid).order_by(EvidenceMaster.code)
    rows = list(session.scalars(stmt).all())
    if master_name_order:
        order = {n: i for i, n in enumerate(master_name_order)}
        rows.sort(key=lambda r: order.get(str(r.name), 999))
    return [_master_to_dict(r) for r in rows]


def insert_evidence_collection(
    session: Session,
    *,
    evidence_id: uuid.UUID,
    evidence_name: str,
    user_id: str,
    tool_evidence: dict[str, Any] | None,
    evidence_from: str = EVIDENCE_FROM_TOOL,
    source: str = "Zoho People API",
    status: str,
    detail: dict[str, Any] | None,
    error_message: str | None,
    started_at: datetime,
    completed_at: datetime,
) -> None:
    te: dict[str, Any] = dict(tool_evidence or {})
    te["_run"] = {
        "status": status,
        "detail": detail,
        "error_message": error_message,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }
    now = datetime.now(timezone.utc)
    session.add(
        EvidenceCollection(
            id=uuid.uuid4(),
            evidence_id=evidence_id,
            evidence_from=evidence_from,
            source=_truncate(source, 255),
            name=_truncate(evidence_name, 255),
            tool_evidence=te,
            updated_by=_truncate(str(user_id), 255),
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()


def insert_evidence_collection_after_failed_collect(
    session: Session,
    *,
    organization_id: str,
    tool_id: str,
    master: dict[str, Any],
    user_id: str,
    tool_evidence: dict[str, Any] | None,
    status: str,
    detail: dict[str, Any] | None,
    error_message: str | None,
    started_at: datetime,
    completed_at: datetime,
) -> None:
    now = datetime.now(timezone.utc)
    oid = _uuid(organization_id)
    tid = _uuid(tool_id)
    title = _truncate(
        str(master.get("name") or master.get("code") or "collection_failed"),
        255,
    )
    code = _truncate(str(master.get("code") or "unknown"), 255)
    eid = uuid.uuid4()
    session.add(
        Evidence(
            id=eid,
            organization_id=oid,
            title=title,
            code=code,
            description=normalize_evidence_master_description(master),
            due_date=None,
            status="failed",
            tool_id=tid,
            created_at=now,
            updated_at=now,
        )
    )
    session.flush()
    insert_evidence_collection(
        session,
        evidence_id=eid,
        evidence_name=title,
        user_id=user_id,
        tool_evidence=tool_evidence,
        evidence_from=EVIDENCE_FROM_TOOL,
        status=status,
        detail=detail,
        error_message=error_message,
        started_at=started_at,
        completed_at=completed_at,
    )


def save_tool_integration_config(session: Session, integration_id: Any, new_cfg: dict[str, Any]) -> None:
    ti = session.get(ToolIntegration, _uuid(integration_id))
    if not ti:
        return
    ti.configuration_data = new_cfg
    ti.is_active = True
    session.commit()
