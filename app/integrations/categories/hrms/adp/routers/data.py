"""ADP: workers list."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.adp import api_client
from app.integrations.categories.hrms.adp.normalize import adp_extract_workers, adp_worker_to_employee
from app.integrations.categories.hrms.adp.session import get_config_and_token

router = APIRouter(prefix="/api/v1/integrations/hrms/adp", tags=["integrations", "hrms", "adp"])


@router.get("/employees")
def list_employees(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_workers(cfg, token, limit=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = adp_extract_workers(raw)
    return {"unified_employees": [adp_worker_to_employee(r).model_dump() for r in rows], "raw": raw}
