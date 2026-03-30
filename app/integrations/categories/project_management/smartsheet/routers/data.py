from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.smartsheet import api_client
from app.integrations.categories.project_management.smartsheet.normalize import ss_row_to_unified, ss_sheet_to_unified, ss_user_to_unified
from app.integrations.categories.project_management.smartsheet.session import get_token

router = APIRouter(prefix="/api/v1/integrations/project-management/smartsheet", tags=["integrations", "project-management", "smartsheet"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    raw = api_client.get_user(token)
    return {"unified": ss_user_to_unified(raw).model_dump(), "raw": raw}


@router.get("/sheets")
def sheets(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    rows = api_client.list_sheets(token)
    return {"unified_projects": [ss_sheet_to_unified(r).model_dump() for r in rows], "raw_sheets": rows}


@router.get("/sheets/{sheet_id}/rows")
def rows(sheet_id: str, org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    rows = api_client.list_rows(token, sheet_id)
    return {"unified_tasks": [ss_row_to_unified(r, sheet_id=sheet_id).model_dump() for r in rows], "raw_rows": rows}
