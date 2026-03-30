"""JumpCloud — system users (normalized)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.jumpcloud import api_client
from app.integrations.categories.idp.jumpcloud.normalize import extract_jumpcloud_users, jumpcloud_user_to_iam
from app.integrations.categories.idp.jumpcloud.session import get_config_and_api_key

router = APIRouter(prefix="/api/v1/integrations/jumpcloud", tags=["integrations", "idp", "jumpcloud"])


@router.get("/users")
def list_users(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    cfg, api_key = get_config_and_api_key(session, org_id, tool_id)
    try:
        raw = api_client.list_system_users(cfg, api_key)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = extract_jumpcloud_users(raw)
    identities = [jumpcloud_user_to_iam(r).model_dump() for r in rows]
    return {"unified_identities": identities, "raw": raw}
