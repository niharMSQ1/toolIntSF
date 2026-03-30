from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.categories.idp.onelogin.credentials import resolve_access_token
from app.integrations.core.persistence import tool_integration_service as persistence


def get_config_and_token(session: Session, org_id: str, tool_id: str) -> tuple[dict[str, Any], str]:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    token = resolve_access_token(cfg)
    if not token:
        raise HTTPException(status_code=400, detail="access_token missing.")
    return cfg, token
