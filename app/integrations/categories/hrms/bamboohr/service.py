"""BambooHR service helpers.

This is the application/service layer for BambooHR.

Why this file matters:
- routers should not know how to load DB integration rows
- API clients should not know about persistence or token refresh
- collectors should not repeat auth/readiness checks

So this file becomes the shared "prepare a usable BambooHR integration" layer.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.hrms.bamboohr import api_client
from app.integrations.categories.hrms.bamboohr.credentials import (
    resolve_access_token,
    resolve_api_key,
    resolve_auth_mode,
    resolve_subdomain,
)
from app.integrations.categories.hrms.bamboohr.token_refresh import ensure_fresh_credentials
from app.integrations.core.persistence import tool_integration_service as persistence


def _load_ready_integration(session: Session, org_id: str, tool_id: str) -> dict[str, Any]:
    """Load a BambooHR integration that is ready for immediate API use.

    This is the BambooHR equivalent of the "ready integration" gate used by the
    other providers. It hides the repetitive steps:
    1. fetch the integration row from DB
    2. refresh tokens if app auth needs it
    3. verify usable credentials exist
    4. return one normalized context dict
    """
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise ValueError("Integration not found; configure the tool first.")

    cfg = ensure_fresh_credentials(session, row)
    mode = resolve_auth_mode(cfg)

    if mode == "api_key":
        if not resolve_api_key(cfg):
            raise ValueError("Complete BambooHR API key setup first (api_key missing).")
    else:
        if not resolve_access_token(cfg):
            raise ValueError("Complete BambooHR app OAuth first (access token missing).")

    return {
        "row": row,
        "cfg": cfg,
        "auth_mode": mode,
        "subdomain": resolve_subdomain(cfg),
    }


def get_employees_directory(session: Session, *, org_id: str, tool_id: str) -> Any:
    """Fetch the BambooHR employee directory using a ready integration context."""
    ready = _load_ready_integration(session, org_id, tool_id)
    return api_client.list_employees_directory(ready["cfg"])


def get_employee(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    employee_id: str,
    fields: list[str] | None = None,
) -> Any:
    """Fetch one BambooHR employee record."""
    ready = _load_ready_integration(session, org_id, tool_id)
    return api_client.get_employee(ready["cfg"], employee_id, fields=fields)
