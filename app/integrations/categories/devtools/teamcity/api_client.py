"""TeamCity REST client (Bearer token)."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from app.integrations.categories.devtools.teamcity.constants import TEAMCITY_REST_PREFIX


def _log(r: httpx.Response) -> None:
    if os.environ.get("TEAMCITY_DEBUG_HTTP"):
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


def get_server(base_url: str, token: str) -> dict[str, Any]:
    return get_json(base_url, token, f"{TEAMCITY_REST_PREFIX}/server")


def list_projects(base_url: str, token: str) -> list[dict[str, Any]]:
    body = get_json(base_url, token, f"{TEAMCITY_REST_PREFIX}/projects")
    proj = body.get("project") if isinstance(body, dict) else None
    if isinstance(proj, list):
        return [x for x in proj if isinstance(x, dict)]
    if isinstance(proj, dict):
        return [proj]
    return []


def list_builds(base_url: str, token: str, *, count: int = 20) -> list[dict[str, Any]]:
    locator = f"count:{count}"
    body = get_json(base_url, token, f"{TEAMCITY_REST_PREFIX}/builds", params={"locator": locator})
    builds = body.get("build") if isinstance(body, dict) else None
    if isinstance(builds, list):
        return [x for x in builds if isinstance(x, dict)]
    return []


def get_build(base_url: str, token: str, build_id: str) -> dict[str, Any]:
    return get_json(base_url, token, f"{TEAMCITY_REST_PREFIX}/builds/id:{build_id}")


def get_build_artifacts(base_url: str, token: str, build_id: str) -> list[dict[str, Any]]:
    body = get_json(base_url, token, f"{TEAMCITY_REST_PREFIX}/builds/id:{build_id}/artifacts/children/")
    file = body.get("file") if isinstance(body, dict) else None
    if isinstance(file, list):
        return [x for x in file if isinstance(x, dict)]
    return []


def validate_connection(base_url: str, token: str) -> bool:
    try:
        get_server(base_url, token)
        return True
    except httpx.HTTPStatusError:
        return False
