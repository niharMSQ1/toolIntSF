"""
Azure DevOps Service Hooks POST target.

Service hook payloads vary by event type; optional shared secret via ``Authorization: Bearer <webhook_secret>``
when you configure your subscription endpoint to require it (custom header patterns may apply in your network).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.azure_devops.normalize import ado_service_hook_to_event
from app.integrations.core.persistence import tool_integration_service as persistence

router = APIRouter(tags=["webhooks", "devtools", "azure-devops"])


@router.post("/api/v1/webhooks/azure-devops/{org_id}/{tool_id}", response_model=None)
async def receive_azure_devops_webhook(
    org_id: str,
    tool_id: str,
    request: Request,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    body = await request.body()
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found for this path.")

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        cfg = {}
    secret = cfg.get("webhook_secret")
    if secret and str(secret).strip():
        auth = request.headers.get("Authorization") or ""
        expected = f"Bearer {str(secret).strip()}"
        if auth.strip() != expected:
            raise HTTPException(status_code=401, detail="Authorization Bearer does not match webhook_secret.")

    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    event_type = request.headers.get("X-AzureDevOps-EventType") or payload.get("eventType")
    ev = ado_service_hook_to_event(payload, event_type=str(event_type) if event_type else None)
    return {
        "ok": True,
        "unified_event": ev.model_dump(),
        "payload": payload,
    }
