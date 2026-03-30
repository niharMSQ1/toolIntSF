"""PingOne Management API (api.pingone.{tld}/v1) HTTP client."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.idp.ping_identity.credentials import resolve_api_base, resolve_environment_id

logger = logging.getLogger("app.integrations.ping_identity")


def _headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }


def get_json(
    api_base: str,
    access_token: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    p = path if path.startswith("/") else f"/{path}"
    base = api_base.rstrip("/")
    url = f"{base}{p}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(access_token), params=params or {})
            logger.debug("PingOne GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not r.content:
                return {}
            return r.json()
    return {}


def list_users(
    cfg: dict[str, Any],
    access_token: str,
    *,
    limit: int = 100,
) -> Any:
    env = resolve_environment_id(cfg)
    base = resolve_api_base(cfg)
    return get_json(
        base,
        access_token,
        f"/environments/{env}/users",
        params={"limit": min(max(limit, 1), 500)},
    )


def list_populations(cfg: dict[str, Any], access_token: str, *, limit: int = 100) -> Any:
    env = resolve_environment_id(cfg)
    base = resolve_api_base(cfg)
    return get_json(
        base,
        access_token,
        f"/environments/{env}/populations",
        params={"limit": min(max(limit, 1), 500)},
    )


def list_applications(cfg: dict[str, Any], access_token: str, *, limit: int = 100) -> Any:
    env = resolve_environment_id(cfg)
    base = resolve_api_base(cfg)
    return get_json(
        base,
        access_token,
        f"/environments/{env}/applications",
        params={"limit": min(max(limit, 1), 500)},
    )


def list_activities(
    cfg: dict[str, Any],
    access_token: str,
    *,
    filter_expr: str,
    limit: int = 100,
) -> Any:
    """
    GET /environments/{envId}/activities — documented to require a filter including a date range
    (e.g. recordedAt or createdAt).
    """
    env = resolve_environment_id(cfg)
    base = resolve_api_base(cfg)
    return get_json(
        base,
        access_token,
        f"/environments/{env}/activities",
        params={"filter": filter_expr, "limit": min(max(limit, 1), 500)},
    )


def validate_connection(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_users(cfg, access_token, limit=1)
        return True
    except httpx.HTTPStatusError:
        return False
