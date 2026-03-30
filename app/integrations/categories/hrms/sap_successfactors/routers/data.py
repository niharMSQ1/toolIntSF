"""SAP SuccessFactors OData: User list (employees)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.sap_successfactors import api_client
from app.integrations.categories.hrms.sap_successfactors.normalize import odata_extract_results, sf_user_to_employee
from app.integrations.categories.hrms.sap_successfactors.session import get_config_and_token

router = APIRouter(
    prefix="/api/v1/integrations/hrms/sap-successfactors",
    tags=["integrations", "hrms", "sap_successfactors"],
)


@router.get("/employees")
def list_employees(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_users(cfg, token, top=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = odata_extract_results(raw)
    return {"unified_employees": [sf_user_to_employee(r).model_dump() for r in rows], "raw": raw}
