"""Asana webhook receiver: handshake (X-Hook-Secret) and signed events."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.asana.webhook_verify import verify_hook_signature
from app.integrations.core.persistence import tool_integration_service as persistence

router = APIRouter(tags=["webhooks", "project-management", "asana"])


@router.post("/api/v1/webhooks/asana/{org_id}/{tool_id}", response_model=None)
async def receive_asana_webhook(
    org_id: str,
    tool_id: str,
    request: Request,
    session: Session = Depends(get_db),
) -> Response | dict[str, object]:
    """
    Handshake: echo X-Hook-Secret and persist it on tool_integrations.configuration_data.webhook_secret.
    Events: verify X-Hook-Signature (HMAC-SHA256) per Asana docs.
    """
    body = await request.body()
    hook_secret_hdr = request.headers.get("X-Hook-Secret")
    sig = request.headers.get("X-Hook-Signature") or ""

    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found for this path.")

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        cfg = {}

    # Handshake: secret header present, no signature on the verification request (per webhooks guide).
    if hook_secret_hdr and not sig.strip():
        new_cfg = dict(cfg)
        new_cfg["webhook_secret"] = str(hook_secret_hdr).strip()
        persistence.save_tool_integration_config(session, row["id"], new_cfg)
        return Response(
            status_code=200,
            headers={"X-Hook-Secret": str(hook_secret_hdr).strip()},
        )

    stored = cfg.get("webhook_secret")
    if not stored or not str(stored).strip():
        raise HTTPException(
            status_code=503,
            detail="webhook_secret missing; complete the webhook handshake (or POST /configure with webhook_secret).",
        )
    if not verify_hook_signature(secret=str(stored).strip(), body=body, signature_header=sig):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Hook-Signature.")

    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}
    events = payload.get("events") if isinstance(payload, dict) else None
    n = len(events) if isinstance(events, list) else 0
    return {"ok": True, "events_count": n, "payload": payload if isinstance(payload, dict) else {}}
