"""TeamCity generic webhook receiver; optional X-Teamcity-Secret."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.devtools.common_schema import DevOpsEvent
from app.integrations.core.persistence import tool_integration_service as persistence

router = APIRouter(tags=["webhooks", "devtools", "teamcity"])


@router.post("/api/v1/webhooks/teamcity/{org_id}/{tool_id}", response_model=None)
async def receive_teamcity_webhook(
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
        hdr = request.headers.get("X-Teamcity-Secret") or ""
        if hdr.strip() != str(secret).strip():
            raise HTTPException(status_code=401, detail="X-Teamcity-Secret does not match webhook_secret.")

    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    b = payload.get("build")
    build_hint = str(b.get("buildId")) if isinstance(b, dict) and b.get("buildId") is not None else None
    ev = DevOpsEvent(
        id=None,
        event_type=build_hint,
        action=None,
        occurred_at=None,
        provider="teamcity",
        raw=payload,
    )
    return {"ok": True, "unified_event": ev.model_dump(), "payload": payload}
