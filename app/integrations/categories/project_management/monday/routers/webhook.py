"""Monday webhook URL verification (challenge) — https://developer.monday.com/api-reference/docs/webhooks"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["webhooks", "project-management", "monday"])


@router.post("/api/v1/webhooks/monday/{org_id}/{tool_id}", response_model=None)
async def receive_monday_webhook(
    org_id: str,
    tool_id: str,
    request: Request,
) -> JSONResponse | dict[str, Any]:
    del org_id, tool_id
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if isinstance(body, dict) and "challenge" in body:
        return JSONResponse({"challenge": body["challenge"]})
    return {"ok": True, "payload": body if isinstance(body, (dict, list)) else {}}
