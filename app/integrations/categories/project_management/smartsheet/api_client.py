"""Smartsheet REST — Bearer token — https://smartsheet.redoc.ly/"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.integrations.categories.project_management.smartsheet.constants import SMARTSHEET_API_BASE

_MAX = 6


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _http(method: str, token: str, path: str, **kw: Any) -> dict[str, Any]:
    url = path if path.startswith("http") else f"{SMARTSHEET_API_BASE}{path}"
    last: httpx.Response | None = None
    for _ in range(_MAX):
        with httpx.Client(timeout=120.0) as client:
            r = client.request(method, url, headers=_headers(token), **kw)
        last = r
        if r.status_code == 429:
            time.sleep(2.0)
            continue
        r.raise_for_status()
        if r.status_code == 204 or not r.content:
            return {}
        return r.json()
    if last:
        last.raise_for_status()
    raise RuntimeError("Smartsheet request failed")


def get_user(token: str) -> dict[str, Any]:
    return _http("GET", token, "/users/me")


def list_sheets(token: str, *, page_size: int = 100) -> list[dict[str, Any]]:
    data = _http("GET", token, "/sheets", params={"pageSize": page_size})
    val = data.get("data")
    if isinstance(val, list):
        return [x for x in val if isinstance(x, dict)]
    return []


def get_sheet(token: str, sheet_id: str) -> dict[str, Any]:
    return _http("GET", token, f"/sheets/{sheet_id}")


def list_rows(token: str, sheet_id: str, *, page_size: int = 500) -> list[dict[str, Any]]:
    data = _http("GET", token, f"/sheets/{sheet_id}/rows", params={"pageSize": page_size})
    val = data.get("data")
    if isinstance(val, list):
        return [x for x in val if isinstance(x, dict)]
    return []
