"""CyberArk Identity — SCIM 2.0 and REST helpers (Bearer token)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.idp.cyberark.credentials import resolve_identity_base_url

logger = logging.getLogger("app.integrations.cyberark")


def _headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/scim+json, application/json",
    }


def get_json(
    base_url: str,
    access_token: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    p = path if path.startswith("/") else f"/{path}"
    url = f"{base_url.rstrip('/')}{p}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(access_token), params=params or {})
            logger.debug("CyberArk GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not r.content:
                return {}
            return r.json()
    return {}


def list_scim_users(
    cfg: dict[str, Any],
    access_token: str,
    *,
    start_index: int = 1,
    count: int = 100,
) -> Any:
    """GET SCIM 2.0 Users — path per CyberArk SCIM management docs."""
    base = resolve_identity_base_url(cfg)
    path = cfg.get("cyberark_scim_users_path") or "/scim/Users"
    if not str(path).startswith("/"):
        path = f"/{path}"
    return get_json(
        base,
        access_token,
        path,
        params={"startIndex": start_index, "count": min(max(count, 1), 500)},
    )


def validate_connection(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_scim_users(cfg, access_token, count=1)
        return True
    except httpx.HTTPStatusError:
        return False
