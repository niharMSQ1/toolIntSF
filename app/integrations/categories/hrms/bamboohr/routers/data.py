"""BambooHR: employees (directory)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.bamboohr import api_client
from app.integrations.categories.hrms.bamboohr.normalize import bamboo_extract_employees, bamboo_row_to_employee
from app.integrations.categories.hrms.bamboohr.session import get_config_and_key

router = APIRouter(prefix="/api/v1/integrations/hrms/bamboohr", tags=["integrations", "hrms", "bamboohr"])


@router.get("/employees")
def list_employees(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    cfg, api_key = get_config_and_key(session, org_id, tool_id)
    try:
        raw = api_client.get_directory(cfg, api_key)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = bamboo_extract_employees(raw)
    return {"unified_employees": [bamboo_row_to_employee(r).model_dump() for r in rows], "raw": raw}
