from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.categories.idp.jumpcloud.credentials import resolve_api_key
from app.integrations.core.persistence import tool_integration_service as persistence


def get_config_and_api_key(session: Session, org_id: str, tool_id: str) -> tuple[dict[str, Any], str]:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    try:
        key = resolve_api_key(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return cfg, key
