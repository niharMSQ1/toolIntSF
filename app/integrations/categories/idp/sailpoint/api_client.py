"""SailPoint IdentityNow V3 API (Bearer JWT)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.idp.sailpoint.credentials import resolve_api_base, resolve_identities_path

logger = logging.getLogger("app.integrations.sailpoint")


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}


def get_json(
    api_base: str,
    access_token: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    p = path if path.startswith("/") else f"/{path}"
    url = f"{api_base.rstrip('/')}{p}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(access_token), params=params or {})
            logger.debug("SailPoint GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not r.content:
                return {}
            return r.json()
    return {}


def list_public_identities(cfg: dict[str, Any], access_token: str, *, limit: int = 250) -> Any:
    base = resolve_api_base(cfg)
    path = resolve_identities_path(cfg)
    return get_json(base, access_token, path, params={"limit": min(max(limit, 1), 250)})


def validate_connection(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_public_identities(cfg, access_token, limit=1)
        return True
    except httpx.HTTPStatusError:
        return False
