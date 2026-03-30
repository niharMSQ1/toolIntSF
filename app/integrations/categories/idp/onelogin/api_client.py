from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.idp.onelogin.credentials import api_origin_for_region, resolve_region, resolve_users_path

logger = logging.getLogger("app.integrations.onelogin")


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}


def get_json(cfg: dict[str, Any], access_token: str, path: str, *, params: dict[str, Any] | None = None) -> Any:
    origin = api_origin_for_region(resolve_region(cfg))
    p = path if path.startswith("/") else f"/{path}"
    url = f"{origin.rstrip('/')}{p}"
    for attempt in range(3):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(access_token), params=params or {})
            logger.debug("OneLogin GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < 2:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not r.content:
                return {}
            return r.json()
    return {}


def list_users(cfg: dict[str, Any], access_token: str) -> Any:
    return get_json(cfg, access_token, resolve_users_path(cfg))


def validate_connection(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_users(cfg, access_token)
        return True
    except httpx.HTTPStatusError:
        return False
