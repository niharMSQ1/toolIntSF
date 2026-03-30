"""Resolve Jenkins credentials from tool integration."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.categories.devtools.jenkins.credentials import (
    resolve_api_token,
    resolve_base_url,
    resolve_username,
)
from app.integrations.core.persistence import tool_integration_service as persistence


def get_api_context(session: Session, org_id: str, tool_id: str) -> dict[str, Any]:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = row["configuration_data"]
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")
    token = resolve_api_token(cfg)
    if not token:
        raise HTTPException(status_code=400, detail="api_token (or jenkins_token) missing in configuration_data.")
    try:
        base_url = resolve_base_url(cfg)
        username = resolve_username(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"base_url": base_url, "username": username, "token": token, "configuration_data": cfg}


def collect_wf_stages(describe: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten Pipeline ``wfapi/describe`` stage trees."""
    out: list[dict[str, Any]] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("name") is not None and ("status" in node or "stageFlowNodes" in node):
                out.append(node)
            subs = node.get("stages")
            if isinstance(subs, list):
                for s in subs:
                    walk(s)
            sfn = node.get("stageFlowNodes")
            if isinstance(sfn, list):
                for s in sfn:
                    walk(s)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(describe.get("stages"))
    return out
