"""Workday: refresh OAuth access token when refresh_token is stored."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.hrms.workday.credentials import (
    has_oauth_client,
    resolve_access_token,
    resolve_hostname,
    resolve_oauth_client,
    resolve_tenant,
)
from app.integrations.categories.hrms.workday.oauth import merge_token_response_into_config, refresh_access_token
from app.integrations.core.persistence import tool_integration_service as persistence
from app.schemas import WorkdayRefreshTokensBody, WorkdayRefreshTokensResponse

router = APIRouter(prefix="/api/v1/integrations/hrms/workday", tags=["integrations", "hrms", "workday"])


@router.post("/refresh-tokens", response_model=WorkdayRefreshTokensResponse)
def refresh_tokens(body: WorkdayRefreshTokensBody, session: Session = Depends(get_db)) -> WorkdayRefreshTokensResponse:
    row = persistence.get_integration(session, body.org_id, body.tool_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found; POST /configure first.")
    cfg = dict(row["configuration_data"])
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=500, detail="Invalid configuration_data")

    if not cfg.get("refresh_token"):
        raise HTTPException(status_code=400, detail="refresh_token not stored; use client credentials configure first.")
    if not has_oauth_client(cfg):
        raise HTTPException(status_code=400, detail="OAuth client_id/client_secret required for refresh.")

    try:
        hostname = resolve_hostname(cfg)
        tenant = resolve_tenant(cfg)
        cid, csec = resolve_oauth_client(cfg)
        payload = refresh_access_token(
            hostname=hostname,
            tenant=tenant,
            client_id=cid,
            client_secret=csec,
            refresh_token=str(cfg["refresh_token"]),
        )
        new_cfg = merge_token_response_into_config(cfg, payload)
        persistence.save_tool_integration_config(session, row["id"], new_cfg)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=e.response.text[:2000]) from e

    masked = dict(new_cfg)
    for k in ("access_token", "refresh_token", "client_secret", "workday_client_secret"):
        if k in masked and masked[k]:
            masked[k] = "***"

    tok = resolve_access_token(new_cfg)
    return WorkdayRefreshTokensResponse(
        ok=True,
        organization_id=body.org_id,
        tool_id=body.tool_id,
        refreshed=bool(tok),
        message="Tokens updated." if tok else "Refresh response did not include access_token.",
        configuration_data=masked,
    )
