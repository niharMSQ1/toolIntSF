"""Workday REST: workers and organizations (normalized)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.workday import api_client
from app.integrations.categories.hrms.workday.normalize import (
    extract_item_list,
    workday_org_to_department,
    workday_worker_to_employee,
)
from app.integrations.categories.hrms.workday.session import get_config_and_token

router = APIRouter(prefix="/api/v1/integrations/hrms/workday", tags=["integrations", "hrms", "workday"])


@router.get("/employees")
def list_employees(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_workers(cfg, token, limit=limit, offset=offset)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = extract_item_list(raw)
    return {
        "unified_employees": [workday_worker_to_employee(r).model_dump() for r in rows],
        "raw": raw,
    }


@router.get("/employees/{worker_id}")
def get_employee(
    worker_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.get_worker(cfg, token, worker_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    if not isinstance(raw, dict):
        raw = {}
    return {"unified": workday_worker_to_employee(raw).model_dump(), "raw": raw}


@router.get("/organizations")
def list_organizations(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    cfg, token = get_config_and_token(session, org_id, tool_id)
    try:
        raw = api_client.list_organizations(cfg, token, limit=limit, offset=offset)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text[:2000]) from e
    rows = extract_item_list(raw)
    return {
        "unified_departments": [workday_org_to_department(r).model_dump() for r in rows],
        "raw": raw,
    }
