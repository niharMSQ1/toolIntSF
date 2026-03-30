"""Google Admin SDK Directory API v1 — users.list."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.idp.google_workspace.credentials import GOOGLE_DIRECTORY_BASE, resolve_workspace_domain

logger = logging.getLogger("app.integrations.google_workspace")


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}


def list_users(
    cfg: dict[str, Any],
    access_token: str,
    *,
    max_results: int = 100,
    page_token: str | None = None,
) -> Any:
    domain = resolve_workspace_domain(cfg)
    params: dict[str, Any] = {"domain": domain, "maxResults": min(max(max_results, 1), 500)}
    if page_token:
        params["pageToken"] = page_token
    url = f"{GOOGLE_DIRECTORY_BASE}/admin/directory/v1/users"
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url, headers=_headers(access_token), params=params)
        logger.debug("Google Directory users.list -> %s", r.status_code)
        r.raise_for_status()
        return r.json()


def validate_connection(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_users(cfg, access_token, max_results=1)
        return True
    except httpx.HTTPStatusError:
        return False
