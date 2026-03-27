"""Explicit ServiceNow evidence collection endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.itsm.servicenow.collection_runner import run_servicenow_evidence_collection
from app.schemas import CollectEvidenceBody, ServiceNowCollectEvidenceResponse

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence", "itsm", "servicenow"])


@router.post("/servicenow/collect", response_model=ServiceNowCollectEvidenceResponse)
def collect_servicenow_evidence(
    body: CollectEvidenceBody,
    session: Session = Depends(get_db),
) -> ServiceNowCollectEvidenceResponse:
    try:
        return run_servicenow_evidence_collection(
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
