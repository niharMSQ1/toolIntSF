"""Load integration row, refresh OAuth when needed, return bearer token."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.categories.project_management.asana.credentials import resolve_bearer_token
from app.integrations.categories.project_management.asana.token_refresh import refresh_asana_access_tokens
from app.integrations.core.persistence import tool_integration_service as persistence


def get_token_and_config(session: Session, org_id: str, tool_id: str) -> tuple[dict[str, Any], str]:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    try:
        cfg, _ = refresh_asana_access_tokens(session, row, force=False)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    token = resolve_bearer_token(cfg)
    if not token:
        raise HTTPException(
            status_code=400,
            detail="No bearer token; set personal_access_token or complete OAuth.",
        )
    return cfg, token
