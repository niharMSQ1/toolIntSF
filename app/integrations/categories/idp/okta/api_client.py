"""Okta Admin API (SSWS) HTTP helpers."""

from __future__ import annotations

from typing import Any

import httpx


def get_json(
    base_url: str,
    path: str,
    api_token: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> Any:
    """GET JSON from Okta Admin API. ``path`` must start with /api/v1/..."""
    base = base_url.rstrip("/")
    p = path if path.startswith("/") else f"/{path}"
    url = f"{base}{p}"
    headers = {
        "Authorization": f"SSWS {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=headers, params=params or {})
        r.raise_for_status()
        if not r.content:
            return {}
        return r.json()


def fetch_org(base_url: str, api_token: str) -> dict[str, Any]:
    """GET /api/v1/org — used to validate token and resolve org."""
    out = get_json(base_url, "/api/v1/org", api_token)
    return out if isinstance(out, dict) else {}
