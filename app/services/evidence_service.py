"""
Create/update evidence using existing evidence + evidence_collections tables only.
Uses evidence.code = canonical evidence_type code, evidence_collections.tool_evidence = normalized payload.
No DB schema changes.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from sqlalchemy import desc, or_

from app.evidence_types import CODE_TO_TYPE, get_evidence_type
from app.models import ControlScenario, Evidence, EvidenceCollection, EvidenceMapped, ScenariosControl

EVIDENCEABLE_TYPE_CONTROL = "App\\Models\\Control"


def _scenarios_for_evidence(db: Session, evidence: Evidence):
    """Find control scenarios that require this evidence (by tool_id + evidence name or code)."""
    if not evidence.tool_id:
        return []
    # Match by display name (evidence.title) or by evidence type code (evidence.code)
    name_or_code = or_(
        ScenariosControl.evidence_name == evidence.title,
        ScenariosControl.evidence_type == evidence.code,
        ScenariosControl.evidence_name == evidence.code,
    )
    scenarios = (
        db.query(ScenariosControl)
        .filter(ScenariosControl.tool_id == evidence.tool_id, name_or_code)
        .all()
    )
    # Also check control_scenarios (same structure, may be where data lives)
    name_or_code_cs = or_(
        ControlScenario.evidence_name == evidence.title,
        ControlScenario.evidence_type == evidence.code,
        ControlScenario.evidence_name == evidence.code,
    )
    control_scenarios = (
        db.query(ControlScenario)
        .filter(ControlScenario.tool_id == evidence.tool_id, name_or_code_cs)
        .all()
    )
    # Collect (control_id,) from both; dedupe
    seen = set()
    out = []
    for sc in scenarios:
        if sc.control_id not in seen:
            seen.add(sc.control_id)
            out.append(sc.control_id)
    for cs in control_scenarios:
        if cs.control_id not in seen:
            seen.add(cs.control_id)
            out.append(cs.control_id)
    return out


def get_or_create_evidence(
    db: Session,
    organization_id: UUID,
    evidence_type_code: str,
    tool_id: UUID,
    title: str | None = None,
) -> Evidence:
    """Find existing Evidence by (organization_id, code, tool_id) or create one."""
    et = get_evidence_type(evidence_type_code)
    display_name = (et.name if et else evidence_type_code) if not title else title

    row = (
        db.query(Evidence)
        .filter(
            Evidence.organization_id == organization_id,
            Evidence.code == evidence_type_code,
            Evidence.tool_id == tool_id,
        )
        .first()
    )
    if row:
        row.updated_at = datetime.utcnow()
        if title:
            row.title = title
        db.commit()
        db.refresh(row)
        return row

    row = Evidence(
        id=uuid4(),
        organization_id=organization_id,
        title=display_name,
        code=evidence_type_code,
        tool_id=tool_id,
        status="collected",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def map_evidence_to_controls(
    db: Session,
    evidence: Evidence,
    mapped_by: str | None = "system",
) -> None:
    """
    Ensure EvidenceMapped rows exist linking this evidence to all controls
    that reference the same tool + evidence (by name or code) in scenarios_control
    or control_scenarios. This lets the UI show which controls are satisfied by a given evidence.
    """
    control_ids = _scenarios_for_evidence(db, evidence)
    if not control_ids:
        return

    now = datetime.utcnow()
    for control_id in control_ids:
        existing = (
            db.query(EvidenceMapped)
            .filter(
                EvidenceMapped.evidence_id == evidence.id,
                EvidenceMapped.evidenceable_type == EVIDENCEABLE_TYPE_CONTROL,
                EvidenceMapped.evidenceable_id == control_id,
            )
            .first()
        )
        if existing:
            continue

        mapping = EvidenceMapped(
            id=uuid4(),
            evidence_id=evidence.id,
            evidenceable_type=EVIDENCEABLE_TYPE_CONTROL,
            evidenceable_id=control_id,
            mapped_by=mapped_by,
            created_at=now,
            updated_at=now,
        )
        db.add(mapping)
    db.commit()


def add_evidence_collection(
    db: Session,
    evidence_id: UUID,
    tool_evidence: dict,
    source: str = "zoho_people",
    evidence_from: str = "document",
    name: str | None = None,
) -> EvidenceCollection:
    """Append one evidence_collections row with normalized payload (one snapshot)."""
    now = datetime.utcnow()
    coll = EvidenceCollection(
        id=uuid4(),
        evidence_id=evidence_id,
        # DB check constraint expects known types like 'document' or 'link' here.
        # Use 'document' for system-collected JSON evidence from tools.
        evidence_from=evidence_from,
        source=source,
        name=name or f"Collection {now.isoformat()}",
        tool_evidence=tool_evidence,
        created_at=now,
        updated_at=now,
    )
    db.add(coll)
    db.commit()
    db.refresh(coll)
    return coll


def get_or_update_evidence_collection(
    db: Session,
    evidence_id: UUID,
    tool_evidence: dict,
    source: str = "zoho_people",
    evidence_from: str = "document",
    name: str | None = None,
) -> EvidenceCollection:
    """
    Update the most recent EvidenceCollection for this evidence (same source) with the new payload.
    If none exists, add one. Use this for syncs so we update in place instead of appending.
    """
    now = datetime.utcnow()
    latest = (
        db.query(EvidenceCollection)
        .filter(
            EvidenceCollection.evidence_id == evidence_id,
            EvidenceCollection.source == source,
        )
        .order_by(desc(EvidenceCollection.updated_at), desc(EvidenceCollection.created_at))
        .first()
    )
    if latest:
        latest.tool_evidence = tool_evidence
        latest.updated_at = now
        if name:
            latest.name = name
        db.commit()
        db.refresh(latest)
        return latest
    return add_evidence_collection(
        db,
        evidence_id=evidence_id,
        tool_evidence=tool_evidence,
        source=source,
        evidence_from=evidence_from,
        name=name,
    )


class EvidenceService:
    """Record normalized evidence into existing evidence + evidence_collections tables."""

    def __init__(self, db: Session):
        self.db = db

    def record_hr_evidence(
        self,
        organization_id: UUID,
        tool_id: UUID,
        evidence_type_code: str,
        payload: dict,
        source: str = "zoho_people",
        collection_name: str | None = None,
        update_existing: bool = True,
    ) -> EvidenceCollection:
        """
        Ensure an Evidence row exists for (org, evidence_type_code, tool_id), then
        update the latest EvidenceCollection (same source) with the payload, or add one if none.
        Set update_existing=False to always append a new collection (legacy behavior).
        """
        if evidence_type_code not in CODE_TO_TYPE:
            raise ValueError(f"Unknown evidence type: {evidence_type_code}")

        evidence = get_or_create_evidence(
            self.db,
            organization_id=organization_id,
            evidence_type_code=evidence_type_code,
            tool_id=tool_id,
        )
        collected_at = payload.get("collected_at") or datetime.utcnow().isoformat()
        name = collection_name or f"{CODE_TO_TYPE[evidence_type_code].name} - {collected_at[:10]}"
        if update_existing:
            coll = get_or_update_evidence_collection(
                self.db,
                evidence_id=evidence.id,
                tool_evidence=payload,
                source=source,
                name=name,
            )
        else:
            coll = add_evidence_collection(
                self.db,
                evidence_id=evidence.id,
                tool_evidence=payload,
                source=source,
                name=name,
            )
        # Map this evidence to all relevant controls via evidence_mappeds.
        map_evidence_to_controls(self.db, evidence)
        return coll
