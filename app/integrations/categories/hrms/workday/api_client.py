"""Workday REST API client (Bearer access token)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.hrms.workday.credentials import resolve_api_version, resolve_hostname, resolve_tenant

logger = logging.getLogger("app.integrations.workday")


def _rest_root(cfg: dict[str, Any]) -> str:
    host = resolve_hostname(cfg)
    tenant = resolve_tenant(cfg)
    ver = resolve_api_version(cfg)
    return f"{host}/api/{ver}/{tenant}"


def _headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }


def request_json(
    method: str,
    cfg: dict[str, Any],
    access_token: str,
    relative_path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: float = 120.0,
    max_retries: int = 2,
) -> Any:
    root = _rest_root(cfg)
    path = relative_path if relative_path.startswith("/") else f"/{relative_path}"
    url = f"{root}{path}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=timeout) as client:
            kwargs: dict[str, Any] = {"headers": _headers(access_token), "params": params or {}}
            if json_body is not None:
                kwargs["json"] = json_body
            r = client.request(method, url, **kwargs)
            logger.debug("Workday %s %s -> %s", method, url, r.status_code)
            if r.status_code == 429 and attempt < max_retries:
                ra = r.headers.get("Retry-After")
                try:
                    time.sleep(float(ra) if ra else 2.0)
                except ValueError:
                    time.sleep(2.0)
                continue
            r.raise_for_status()
            if not (r.text or "").strip():
                return {}
            return r.json()
    return {}


def get_json(
    cfg: dict[str, Any],
    access_token: str,
    relative_path: str,
    *,
    params: dict[str, Any] | None = None,
) -> Any:
    return request_json("GET", cfg, access_token, relative_path, params=params)


def list_workers(
    cfg: dict[str, Any],
    access_token: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> Any:
    """GET ``/workers`` — resource path per Workday REST API."""
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    return get_json(cfg, access_token, "/workers", params=params)


def get_worker(cfg: dict[str, Any], access_token: str, worker_id: str) -> Any:
    from urllib.parse import quote

    wid = quote(worker_id, safe="")
    return get_json(cfg, access_token, f"/workers/{wid}")


def list_organizations(
    cfg: dict[str, Any],
    access_token: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> Any:
    """GET ``/organizations`` when enabled for the tenant (may 404 if not subscribed)."""
    return get_json(cfg, access_token, "/organizations", params={"limit": limit, "offset": offset})


def validate_token_with_workers(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_workers(cfg, access_token, limit=1, offset=0)
        return True
    except httpx.HTTPStatusError:
        return False
