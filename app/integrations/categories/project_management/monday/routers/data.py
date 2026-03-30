"""Monday GraphQL-backed data API (unified schema)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.monday import api_client
from app.integrations.categories.project_management.monday.normalize import (
    monday_board_to_unified,
    monday_item_to_unified,
    monday_user_to_unified,
)
from app.integrations.categories.project_management.monday.session import get_token

router = APIRouter(
    prefix="/api/v1/integrations/project-management/monday",
    tags=["integrations", "project-management", "monday"],
)


@router.get("/me")
def monday_me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    raw = api_client.get_me(token)
    if not raw:
        raise HTTPException(status_code=502, detail="Unexpected me response.")
    u = monday_user_to_unified(raw)
    return {"unified": u.model_dump(), "raw": raw}


@router.get("/boards")
def monday_boards(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 50,
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    rows = api_client.list_boards(token, limit=limit)
    unified = [monday_board_to_unified(r).model_dump() for r in rows]
    return {"unified_boards": unified, "raw_boards": rows}


@router.get("/boards/{board_id}/items")
def monday_board_items(
    board_id: str,
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    limit: int = 100,
) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    rows = api_client.list_items_for_board(token, board_id, limit=limit)
    unified = [monday_item_to_unified(r, board_id=board_id).model_dump() for r in rows]
    return {"unified_tasks": unified, "raw_items": rows}
