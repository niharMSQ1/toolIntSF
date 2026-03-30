"""CyberArk Identity — SCIM users (normalized)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.cyberark import api_client
from app.integrations.categories.idp.cyberark.normalize import extract_scim_users, scim_user_to_identity
from app.integrations.categories.idp.cyberark.session import get_config_and_token

router = APIRouter(prefix="/api/v1/integrations/cyberark-identity", tags=["integrations", "idp", "cyberark"])


@router.get("/users")
def list_users(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 100,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_scim_users(cfg, token, count=min(max(limit, 1), 500))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = extract_scim_users(raw)
    identities = [scim_user_to_identity(r).model_dump() for r in rows]
    return {"unified_identities": identities, "raw": raw}
