"""Argo CD REST client (Authorization: Bearer)."""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.categories.devtools.argocd.constants import ARGOCD_API_PREFIX


def _log(r: httpx.Response) -> None:
    if os.environ.get("ARGOCD_DEBUG_HTTP"):
        print(r.status_code, (r.text or "")[:1200])


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def get_json(
    base_url: str,
    token: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    path = path if path.startswith("/") else f"/{path}"
    url = f"{base_url.rstrip('/')}{path}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(token), params=params or {})
            _log(r)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not (r.text or "").strip():
                return {}
            return r.json()
    return {}


def get_version(base_url: str, token: str) -> dict[str, Any]:
    return get_json(base_url, token, f"{ARGOCD_API_PREFIX}/version")


def get_account(base_url: str, token: str) -> dict[str, Any]:
    return get_json(base_url, token, f"{ARGOCD_API_PREFIX}/account")


def list_applications(base_url: str, token: str, *, limit: int = 100) -> list[dict[str, Any]]:
    body = get_json(base_url, token, f"{ARGOCD_API_PREFIX}/applications", params={"limit": limit})
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    items = body.get("items") if isinstance(body, dict) else None
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict)]


def get_application(base_url: str, token: str, name: str) -> dict[str, Any]:
    enc = quote(name, safe="")
    return get_json(base_url, token, f"{ARGOCD_API_PREFIX}/applications/{enc}")


def validate_connection(base_url: str, token: str) -> bool:
    try:
        get_version(base_url, token)
        return True
    except httpx.HTTPStatusError:
        return False
