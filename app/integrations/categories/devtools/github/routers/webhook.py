"""GitHub webhooks: verify X-Hub-Signature-256 and return normalized event metadata."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.github.normalize import github_webhook_to_event
from app.integrations.categories.devtools.github.webhook_verify import verify_github_webhook_signature
from app.integrations.core.persistence import tool_integration_service as persistence

router = APIRouter(tags=["webhooks", "devtools", "github"])


@router.post("/api/v1/webhooks/github/{org_id}/{tool_id}", response_model=None)
async def receive_github_webhook(
    org_id: str,
    tool_id: str,
    request: Request,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256") or ""
    event_name = request.headers.get("X-GitHub-Event")
    delivery = request.headers.get("X-GitHub-Delivery")

    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found for this path.")

    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        cfg = {}
    secret = cfg.get("webhook_secret")
    if not secret or not str(secret).strip():
        raise HTTPException(
            status_code=503,
            detail="webhook_secret missing in configuration_data; set it to the repository webhook secret.",
        )

    if not verify_github_webhook_signature(secret=str(secret).strip(), body=body, signature_header=sig):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Hub-Signature-256.")

    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    ev = github_webhook_to_event(
        event_name=str(event_name) if event_name else None,
        delivery_id=str(delivery) if delivery else None,
        payload=payload,
    )
    return {
        "ok": True,
        "unified_event": ev.model_dump(),
        "github_event": event_name,
        "delivery_id": delivery,
        "payload": payload,
    }
