"""OneLogin — users (normalized)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.onelogin import api_client
from app.integrations.categories.idp.onelogin.normalize import extract_onelogin_users, onelogin_user_to_iam
from app.integrations.categories.idp.onelogin.session import get_config_and_token

router = APIRouter(prefix="/api/v1/integrations/onelogin", tags=["integrations", "idp", "onelogin"])


@router.get("/users")
def list_users(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_users(cfg, token)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = extract_onelogin_users(raw)
    identities = [onelogin_user_to_iam(r).model_dump() for r in rows]
    return {"unified_identities": identities, "raw": raw}
