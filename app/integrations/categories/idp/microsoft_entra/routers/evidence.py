"""Evidence collection for Microsoft Entra (commercial + GCC High)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.microsoft_entra.collection_runner import run_entra_evidence_collection
from app.integrations.categories.idp.microsoft_entra.credentials import resolve_national_cloud
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import CollectEvidenceBody, CollectEvidenceResponse

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence", "idp", "microsoft_entra"])


def _collect_impl(body: CollectEvidenceBody, session: Session, *, cloud: NationalCloud) -> CollectEvidenceResponse:
    row = persistence.get_integration(session, body.org_id, body.tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row.get("configuration_data")
    if isinstance(cfg, dict) and resolve_national_cloud(cfg) != cloud:
        raise HTTPException(
            status_code=400,
            detail="Use /evidence/entra/collect or /evidence/entra-gcc-high/collect to match this integration.",
        )
    try:
        return run_entra_evidence_collection(
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


@router.post("/entra/collect", response_model=CollectEvidenceResponse)
def collect_evidence_entra_commercial(
    body: CollectEvidenceBody, session: Session = Depends(get_db)
) -> CollectEvidenceResponse:
    return _collect_impl(body, session, cloud=NationalCloud.COMMERCIAL)


@router.post("/entra-gcc-high/collect", response_model=CollectEvidenceResponse)
def collect_evidence_entra_gcc_high(
    body: CollectEvidenceBody, session: Session = Depends(get_db)
) -> CollectEvidenceResponse:
    return _collect_impl(body, session, cloud=NationalCloud.GCC_HIGH)
