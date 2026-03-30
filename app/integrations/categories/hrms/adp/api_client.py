"""ADP REST API (Workers API path — verify against your ADP API subscription)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.hrms.adp.credentials import resolve_api_base

logger = logging.getLogger("app.integrations.adp")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def get_json(
    api_base: str,
    access_token: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    path = path if path.startswith("/") else f"/{path}"
    url = f"{api_base.rstrip('/')}{path}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(access_token), params=params or {})
            logger.debug("ADP GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not (r.text or "").strip():
                return {}
            return r.json()
    return {}


def list_workers(cfg: dict[str, Any], access_token: str, *, limit: int = 50) -> Any:
    """GET ``/hr/v2/workers`` — path per ADP Human Resources API (subscription-dependent)."""
    base = resolve_api_base(cfg)
    return get_json(base, access_token, "/hr/v2/workers", params={"$top": limit})


def validate_connection(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_workers(cfg, access_token, limit=1)
        return True
    except httpx.HTTPStatusError:
        return False
