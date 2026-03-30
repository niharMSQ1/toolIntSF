"""Notion REST — Bearer integration token + Notion-Version header."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.integrations.categories.project_management.notion.constants import NOTION_API_BASE, NOTION_VERSION

_MAX = 6


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _request(method: str, token: str, path: str, *, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
    url = path if path.startswith("http") else f"{NOTION_API_BASE}{path}"
    last: httpx.Response | None = None
    for _ in range(_MAX):
        with httpx.Client(timeout=120.0) as client:
            r = client.request(
                method,
                url,
                headers=_headers(token),
                content=json.dumps(json_body) if json_body is not None else None,
            )
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
    raise RuntimeError("Notion request failed")


def get_me(token: str) -> dict[str, Any]:
    return _request("GET", token, "/users/me")


def search(token: str, *, page_size: int = 100) -> list[dict[str, Any]]:
    body = {"page_size": page_size}
    data = _request("POST", token, "/search", json_body=body)
    res = data.get("results")
    if isinstance(res, list):
        return [x for x in res if isinstance(x, dict)]
    return []


def get_page(token: str, page_id: str) -> dict[str, Any]:
    return _request("GET", token, f"/pages/{page_id}")
