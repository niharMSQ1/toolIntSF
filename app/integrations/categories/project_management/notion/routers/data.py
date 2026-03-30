from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.project_management.notion import api_client
from app.integrations.categories.project_management.notion.normalize import notion_page_to_unified_task, notion_user_to_unified
from app.integrations.categories.project_management.notion.session import get_token

router = APIRouter(prefix="/api/v1/integrations/project-management/notion", tags=["integrations", "project-management", "notion"])


@router.get("/me")
def me(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    raw = api_client.get_me(token)
    return {"unified": notion_user_to_unified(raw).model_dump(), "raw": raw}


@router.get("/search")
def search(org_id: str, tool_id: str, session: Session = Depends(get_db), page_size: int = 50) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    rows = api_client.search(token, page_size=min(page_size, 100))
    unified = []
    for r in rows:
        obj = r.get("object")
        if obj == "page":
            unified.append(notion_page_to_unified_task(r).model_dump())
        elif obj == "database":
            unified.append(notion_page_to_unified_task(r).model_dump())
    return {"unified_items": unified, "raw_results": rows}


@router.get("/pages/{page_id}")
def page(page_id: str, org_id: str, tool_id: str, session: Session = Depends(get_db)) -> dict[str, object]:
    token = get_token(session, org_id, tool_id)
    raw = api_client.get_page(token, page_id)
    return {"unified": notion_page_to_unified_task(raw).model_dump(), "raw": raw}
