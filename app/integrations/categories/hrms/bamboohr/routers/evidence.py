"""Evidence collection API for BambooHR-backed integrations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.bamboohr.collection_runner import run_bamboohr_evidence_collection
from app.schemas import CollectEvidenceBody, CollectEvidenceResponse

router = APIRouter(prefix="/api/v1/evidence/bamboohr", tags=["evidence", "hrms", "bamboohr"])


@router.post("/collect", response_model=CollectEvidenceResponse)
def collect_evidence(body: CollectEvidenceBody, session: Session = Depends(get_db)) -> CollectEvidenceResponse:
    """Collect BambooHR evidence using the stored auth mode and credentials."""
    try:
        return run_bamboohr_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower() or "no bamboohr evidence_masters" in msg.lower():
            raise HTTPException(status_code=404, detail=msg) from e
        raise HTTPException(status_code=400, detail=msg) from e
