"""BambooHR API client (directory / employees)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.hrms.bamboohr.credentials import basic_auth_header, resolve_subdomain

logger = logging.getLogger("app.integrations.bamboohr")


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": basic_auth_header(api_key), "Accept": "application/json"}


def get_json(
    subdomain: str,
    api_key: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    path = path if path.startswith("/") else f"/{path}"
    url = f"https://{subdomain}.bamboohr.com/api/v1{path}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(api_key), params=params or {})
            logger.debug("BambooHR GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not (r.text or "").strip():
                return {}
            return r.json()
    return {}


def get_directory(cfg: dict[str, Any], api_key: str) -> Any:
    sub = resolve_subdomain(cfg)
    return get_json(sub, api_key, "/employees/directory")


def validate_connection(cfg: dict[str, Any], api_key: str) -> bool:
    try:
        get_directory(cfg, api_key)
        return True
    except httpx.HTTPStatusError:
        return False
