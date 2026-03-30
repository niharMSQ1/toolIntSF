"""CircleCI API context."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.categories.devtools.circleci.credentials import (
    resolve_base_url,
    resolve_project_slug,
    resolve_token,
)
from app.integrations.core.persistence import tool_integration_service as persistence


def get_api_context(session: Session, org_id: str, tool_id: str) -> dict[str, Any]:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    token = resolve_token(cfg)
    if not token:
        raise HTTPException(status_code=400, detail="circleci_token missing in configuration_data.")
    base_url = resolve_base_url(cfg)
    return {"token": token, "base_url": base_url, "configuration_data": cfg}


def project_slug_or_query(cfg: dict[str, Any], project: str | None) -> str:
    if project and str(project).strip():
        return str(project).strip()
    s = resolve_project_slug(cfg)
    if not s:
        raise HTTPException(
            status_code=400,
            detail="project_slug required in configuration_data or pass ?project= (e.g. gh/org/repo).",
        )
    return s
