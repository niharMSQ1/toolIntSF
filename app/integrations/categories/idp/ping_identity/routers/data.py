"""Read-only directory data (normalized identities) from PingOne Management API."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.ping_identity import api_client
from app.integrations.categories.idp.ping_identity.normalize import extract_users, ping_user_to_identity
from app.integrations.categories.idp.ping_identity.session import get_config_and_token

router = APIRouter(prefix="/api/v1/integrations/ping-identity", tags=["integrations", "idp", "ping_identity"])


@router.get("/users")
def list_users_normalized(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_users(cfg, token, limit=min(max(limit, 1), 200))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = extract_users(raw)
    identities = [ping_user_to_identity(r).model_dump() for r in rows]
    return {"unified_identities": identities, "raw": raw}
