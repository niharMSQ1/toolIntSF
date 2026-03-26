"""Unified sync API for all tool integrations (manual + cron)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.core.sync_dispatch import run_integration_sync
from app.schemas import SyncIntegrationBody, SyncIntegrationResponse

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations", "sync"])


@router.post("/sync", response_model=SyncIntegrationResponse)
def sync_integration(body: SyncIntegrationBody, session: Session = Depends(get_db)) -> SyncIntegrationResponse:
    """
    Pull fresh evidence for a configured integration (same work as provider-specific collect endpoints).

    Use for **manual refresh** or **scheduled jobs** (cron). Resolves the integration type from
    ``provider_key`` or from ``evidence_masters.source`` for this tool's domain (via ``tool_id``).
    """
    try:
        return run_integration_sync(session, body)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower() or "could not determine" in msg.lower() or "no evidence_masters" in msg.lower():
            raise HTTPException(status_code=404, detail=msg) from e
        raise HTTPException(status_code=400, detail=msg) from e
