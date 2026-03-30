"""Rippling REST API client (Bearer)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.hrms.rippling.credentials import resolve_api_base, resolve_employees_path

logger = logging.getLogger("app.integrations.rippling")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def get_json(
    api_base: str,
    bearer: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    path = path if path.startswith("/") else f"/{path}"
    url = f"{api_base.rstrip('/')}{path}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(bearer), params=params or {})
            logger.debug("Rippling GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not (r.text or "").strip():
                return {}
            return r.json()
    return {}


def list_employees(cfg: dict[str, Any], bearer: str, *, limit: int = 50) -> Any:
    base = resolve_api_base(cfg)
    path = resolve_employees_path(cfg)
    return get_json(base, bearer, path, params={"limit": limit})


def validate_connection(cfg: dict[str, Any], bearer: str) -> bool:
    try:
        list_employees(cfg, bearer, limit=1)
        return True
    except httpx.HTTPStatusError:
        return False
