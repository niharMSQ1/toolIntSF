"""Custom webhook for SAP SuccessFactors-related events (optional Bearer secret)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.sap_successfactors.normalize import sf_webhook_to_event
from app.integrations.core.persistence import tool_integration_service as persistence

router = APIRouter(tags=["webhooks", "hrms", "sap_successfactors"])


@router.post("/api/v1/webhooks/sap-successfactors/{org_id}/{tool_id}", response_model=None)
async def receive_webhook(
    org_id: str,
    tool_id: str,
    request: Request,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    body = await request.body()
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        cfg = {}
    secret = cfg.get("webhook_secret")
    if secret and str(secret).strip():
        auth = request.headers.get("Authorization") or ""
        if auth.strip() != f"Bearer {str(secret).strip()}":
            raise HTTPException(status_code=401, detail="Invalid Authorization.")
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    ev = sf_webhook_to_event(payload)
    return {"ok": True, "unified_event": ev.model_dump(), "payload": payload}
