from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.idp.jumpcloud.credentials import JUMPCLOUD_API_ORIGIN, resolve_users_path

logger = logging.getLogger("app.integrations.jumpcloud")


def _headers(api_key: str) -> dict[str, str]:
    return {"x-api-key": api_key, "Accept": "application/json", "Content-Type": "application/json"}


def get_json(api_key: str, path: str, *, params: dict[str, Any] | None = None) -> Any:
    p = path if path.startswith("/") else f"/{path}"
    url = f"{JUMPCLOUD_API_ORIGIN.rstrip('/')}{p}"
    for attempt in range(3):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(api_key), params=params or {})
            logger.debug("JumpCloud GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < 2:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not r.content:
                return []
            return r.json()
    return []


def list_system_users(cfg: dict[str, Any], api_key: str) -> Any:
    return get_json(api_key, resolve_users_path(cfg))


def validate_connection(cfg: dict[str, Any], api_key: str) -> bool:
    try:
        list_system_users(cfg, api_key)
        return True
    except httpx.HTTPStatusError:
        return False
