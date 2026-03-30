"""UKG: people list."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.ukg import api_client
from app.integrations.categories.hrms.ukg.normalize import ukg_extract_people, ukg_person_to_employee
from app.integrations.categories.hrms.ukg.session import get_config_and_token

router = APIRouter(prefix="/api/v1/integrations/hrms/ukg", tags=["integrations", "hrms", "ukg"])


@router.get("/employees")
def list_employees(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_people(cfg, token, limit=min(max(limit, 1), 200))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = ukg_extract_people(raw)
    return {"unified_employees": [ukg_person_to_employee(r).model_dump() for r in rows], "raw": raw}
