"""
Control evaluation engine: evaluates compliance rules against collected evidence
and persists results to ControlResults.
"""
import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from HRMS_Integrations.db import get_db
from models import ControlResults, Controls, Employees, Evidence, EvidenceCollections


router = APIRouter(prefix="/evaluate", tags=["Control evaluation"])


class OffboardingTicketEvaluationRequest(BaseModel):
    organization_id: uuid.UUID
    control_id: uuid.UUID


class AccessRemoved24hEvaluationRequest(BaseModel):
    organization_id: uuid.UUID
    control_id: uuid.UUID


def _get_leavers(db: Session, organization_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Employees with date_of_exit set and <= today (normalized to date for comparison)."""
    today = datetime.datetime.utcnow().date()
    stmt = (
        select(Employees)
        .where(Employees.organization_id == organization_id)
        .where(Employees.date_of_exit.isnot(None))
    )
    rows = list(db.scalars(stmt).all())
    leavers = []
    for r in rows:
        exit_date = r.date_of_exit
        if exit_date and getattr(exit_date, "date", exit_date) <= today:
            leavers.append({
                "email": r.email,
                "name": r.name,
                "date_of_exit": r.date_of_exit.isoformat() if r.date_of_exit else None,
            })
    return leavers


def _get_latest_offboarding_requests(db: Session, organization_id: uuid.UUID) -> Tuple[List[Dict[str, Any]], List[uuid.UUID]]:
    """
    Get classified offboarding requests from the most recent Jira evidence for this org.
    Returns (list of offboarding request items with requester_email, etc.), list of evidence_ids used.
    """
    stmt = (
        select(Evidence)
        .where(Evidence.organization_id == organization_id)
        .order_by(Evidence.created_at.desc())
    )
    evidence_rows = list(db.scalars(stmt).all())
    for ev in evidence_rows:
        coll_stmt = (
            select(EvidenceCollections)
            .where(EvidenceCollections.evidence_id == ev.id)
            .where(EvidenceCollections.name.in_(["Offboarding Requests", "Customer Requests"]))
        )
        colls = list(db.scalars(coll_stmt).all())
        for c in colls:
            payload = c.tool_evidence or {}
            offboarding = payload.get("classified_offboarding")
            classified = payload.get("classified_requests")
            if offboarding:
                return list(offboarding), [ev.id]
            if classified:
                return [x for x in classified if x.get("is_offboarding")], [ev.id]
    return [], []


def evaluate_offboarding_ticket_per_leaver(
    db: Session,
    organization_id: uuid.UUID,
    control_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Control: Offboarding ticket exists for every leaver.
    For each employee with date_of_exit <= today, check at least one offboarding request
    is linkable by requester_email (or correlation field). Return result and details.
    """
    leavers = _get_leavers(db, organization_id)
    offboarding_requests, evidence_ids = _get_latest_offboarding_requests(db, organization_id)

    # Build set of requester emails from offboarding requests (normalize to lower for match)
    requester_emails = { (r.get("requester_email") or "").strip().lower() for r in offboarding_requests if r.get("requester_email") }

    leavers_without_ticket: List[str] = []
    for leaver in leavers:
        email = (leaver.get("email") or "").strip().lower()
        if not email:
            continue
        if email not in requester_emails:
            leavers_without_ticket.append(leaver.get("email") or email)

    if not leavers:
        result = "PASS"
        details = {"message": "No leavers in scope", "leaver_count": 0}
    elif leavers_without_ticket:
        result = "FAIL"
        details = {
            "message": "One or more leavers have no offboarding ticket",
            "leaver_count": len(leavers),
            "leavers_without_ticket": leavers_without_ticket,
            "offboarding_ticket_count": len(offboarding_requests),
        }
    else:
        result = "PASS"
        details = {
            "message": "Every leaver has at least one offboarding ticket",
            "leaver_count": len(leavers),
            "offboarding_ticket_count": len(offboarding_requests),
        }

    return {
        "result": result,
        "details": details,
        "evidence_ids": evidence_ids,
    }


def run_and_persist_offboarding_ticket_control(
    db: Session,
    organization_id: uuid.UUID,
    control_id: uuid.UUID,
) -> ControlResults:
    """
    Run "Offboarding ticket for every leaver" evaluator and persist to ControlResults.
    """
    run_at = datetime.datetime.utcnow()
    evaluation = evaluate_offboarding_ticket_per_leaver(db, organization_id, control_id)

    row = ControlResults(
        id=uuid.uuid4(),
        organization_id=organization_id,
        control_id=control_id,
        run_at=run_at,
        result=evaluation["result"],
        details=evaluation["details"],
        evidence_ids=evaluation.get("evidence_ids") or [],
        created_at=run_at,
    )
    db.add(row)
    return row


@router.post("/offboarding-ticket-per-leaver", response_model=dict)
def run_offboarding_ticket_per_leaver(
    body: OffboardingTicketEvaluationRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Run control: Offboarding ticket exists for every leaver.
    Persists result to ControlResults. Requires control_id (e.g. the control
    that represents this requirement) and organization_id.
    """
    control = db.get(Controls, body.control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    try:
        row = run_and_persist_offboarding_ticket_control(
            db=db,
            organization_id=body.organization_id,
            control_id=body.control_id,
        )
        db.commit()
        db.refresh(row)
    except Exception:
        db.rollback()
        raise
    return {
        "control_result_id": str(row.id),
        "organization_id": str(row.organization_id),
        "control_id": str(row.control_id),
        "result": row.result,
        "run_at": row.run_at.isoformat() if row.run_at else None,
        "details": row.details,
    }


def evaluate_access_removed_within_24h(
    db: Session,
    organization_id: uuid.UUID,
    control_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Control: Access must be removed within 24 hours of termination.
    Requires HRMS + ITSM + IdP evidence. When IdP is not integrated, returns PENDING_IDP.
    """
    return {
        "result": "PENDING_IDP",
        "details": {
            "message": "IdP integration required to evaluate account disabled status and timing.",
            "evidence_sources_required": ["HRMS", "ITSM", "Identity Provider"],
        },
        "evidence_ids": [],
    }


def run_and_persist_access_removed_24h(
    db: Session,
    organization_id: uuid.UUID,
    control_id: uuid.UUID,
) -> ControlResults:
    """Persist PENDING_IDP (or future PASS/FAIL) for Access removed within 24h control."""
    run_at = datetime.datetime.utcnow()
    evaluation = evaluate_access_removed_within_24h(db, organization_id, control_id)
    row = ControlResults(
        id=uuid.uuid4(),
        organization_id=organization_id,
        control_id=control_id,
        run_at=run_at,
        result=evaluation["result"],
        details=evaluation["details"],
        evidence_ids=evaluation.get("evidence_ids") or [],
        created_at=run_at,
    )
    db.add(row)
    return row


@router.post("/access-removed-within-24h", response_model=dict)
def run_access_removed_within_24h(
    body: AccessRemoved24hEvaluationRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Run control: Access removed within 24 hours of termination.
    Returns PENDING_IDP until an Identity Provider (Okta, Entra ID, etc.) is integrated.
    Persists result to ControlResults.
    """
    control = db.get(Controls, body.control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    try:
        row = run_and_persist_access_removed_24h(
            db=db,
            organization_id=body.organization_id,
            control_id=body.control_id,
        )
        db.commit()
        db.refresh(row)
    except Exception:
        db.rollback()
        raise
    return {
        "control_result_id": str(row.id),
        "organization_id": str(row.organization_id),
        "control_id": str(row.control_id),
        "result": row.result,
        "run_at": row.run_at.isoformat() if row.run_at else None,
        "details": row.details,
    }
