"""BambooHR employee preview/read routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.bamboohr import service
from app.schemas import BambooEmployeeDirectoryResponse, BambooEmployeeResponse

router = APIRouter(prefix="/api/v1/integrations/bamboohr", tags=["integrations", "hrms", "bamboohr"])


def _as_dict(payload: Any) -> dict[str, Any]:
    """Normalize BambooHR API responses into JSON-object form for our response models."""
    if isinstance(payload, dict):
        return payload
    return {"value": payload}


@router.get("/employees/directory", response_model=BambooEmployeeDirectoryResponse)
def bamboohr_employees_directory(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> BambooEmployeeDirectoryResponse:
    try:
        data = service.get_employees_directory(session, org_id=org_id, tool_id=tool_id)
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e

    return BambooEmployeeDirectoryResponse(
        organization_id=org_id,
        tool_id=tool_id,
        data=_as_dict(data),
    )


@router.get("/employees/{employee_id}", response_model=BambooEmployeeResponse)
def bamboohr_employee_detail(
    employee_id: str,
    org_id: str,
    tool_id: str,
    fields: list[str] | None = Query(default=None),
    session: Session = Depends(get_db),
) -> BambooEmployeeResponse:
    try:
        data = service.get_employee(
            session,
            org_id=org_id,
            tool_id=tool_id,
            employee_id=employee_id,
            fields=fields,
        )
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e

    return BambooEmployeeResponse(
        organization_id=org_id,
        tool_id=tool_id,
        employee_id=employee_id,
        data=_as_dict(data),
    )
