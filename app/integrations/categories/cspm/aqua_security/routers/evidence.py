"""Evidence collection API for Aqua Security."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.cspm.aqua_security.collection_runner import run_aqua_security_evidence_collection
from app.schemas import CollectEvidenceBody, CollectEvidenceResponse

router = APIRouter(prefix="/api/v1/evidence/aqua-security", tags=["evidence", "cspm", "aqua-security"])


@router.post("/collect", response_model=CollectEvidenceResponse)
def collect_evidence(body: CollectEvidenceBody, session: Session = Depends(get_db)) -> CollectEvidenceResponse:
    try:
        return run_aqua_security_evidence_collection(
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
        if "not found" in msg.lower() or "no evidence_masters" in msg.lower():
            raise HTTPException(status_code=404, detail=msg) from e
        raise HTTPException(status_code=400, detail=msg) from e
