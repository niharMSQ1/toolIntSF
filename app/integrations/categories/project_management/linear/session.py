from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.categories.project_management.linear.credentials import resolve_api_key
from app.integrations.core.persistence import tool_integration_service as persistence


def get_key(session: Session, org_id: str, tool_id: str) -> str:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    k = resolve_api_key(cfg)
    if not k:
        raise HTTPException(status_code=400, detail="Missing api_key (Linear personal API key).")
    return k
