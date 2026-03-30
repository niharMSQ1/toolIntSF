"""Resolve Azure DevOps config + PAT for API calls."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.categories.devtools.azure_devops.credentials import (
    resolve_api_version,
    resolve_base_url,
    resolve_organization,
    resolve_pat,
    resolve_project,
)
from app.integrations.core.persistence import tool_integration_service as persistence


def get_api_context(session: Session, org_id: str, tool_id: str) -> dict[str, Any]:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    pat = resolve_pat(cfg)
    if not pat:
        raise HTTPException(status_code=400, detail="Azure DevOps PAT missing in configuration_data.")
    try:
        organization = resolve_organization(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    project = resolve_project(cfg)
    base_url = resolve_base_url(cfg)
    api_version = resolve_api_version(cfg)
    return {
        "pat": pat,
        "organization": organization,
        "project": project,
        "base_url": base_url,
        "api_version": api_version,
        "configuration_data": cfg,
    }


def require_project(ctx: dict[str, Any]) -> str:
    p = ctx.get("project")
    if not p:
        raise HTTPException(
            status_code=400,
            detail="project is required in configuration_data for this route (or pass project query param).",
        )
    return str(p)
