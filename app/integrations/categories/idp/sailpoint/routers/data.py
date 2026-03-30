"""SailPoint IdentityNow — public identities (normalized)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.sailpoint import api_client
from app.integrations.categories.idp.sailpoint.normalize import extract_identities, sailpoint_identity_to_iam
from app.integrations.categories.idp.sailpoint.session import get_config_and_token

router = APIRouter(prefix="/api/v1/integrations/sailpoint-identity", tags=["integrations", "idp", "sailpoint"])


@router.get("/users")
def list_users(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 100,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_public_identities(cfg, token, limit=min(max(limit, 1), 250))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = extract_identities(raw)
    return {"unified_identities": [sailpoint_identity_to_iam(r).model_dump() for r in rows], "raw": raw}
