from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.idp.google_workspace import api_client
from app.integrations.categories.idp.google_workspace.normalize import extract_google_users, google_user_to_iam
from app.integrations.categories.idp.google_workspace.session import get_config_and_token

router = APIRouter(prefix="/api/v1/integrations/google-workspace", tags=["integrations", "idp", "google_workspace"])


@router.get("/users")
def list_users(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    max_results: int = 100,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_users(cfg, token, max_results=min(max(max_results, 1), 500))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = extract_google_users(raw)
    return {"unified_identities": [google_user_to_iam(r).model_dump() for r in rows], "raw": raw}
