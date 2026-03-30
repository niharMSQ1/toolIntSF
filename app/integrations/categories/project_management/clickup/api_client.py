"""ClickUp REST — Authorization: <token> — https://clickup.com/api"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.integrations.categories.project_management.clickup.constants import CLICKUP_API_BASE

_MAX = 6


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": token, "Accept": "application/json"}


def _get(token: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{CLICKUP_API_BASE}{path}" if not path.startswith("http") else path
    last: httpx.Response | None = None
    for _ in range(_MAX):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(token), params=params)
        last = r
        if r.status_code == 429:
            time.sleep(2.0)
            continue
        r.raise_for_status()
        return r.json()
    if last:
        last.raise_for_status()
    raise RuntimeError("ClickUp request failed")


def get_user(token: str) -> dict[str, Any]:
    return _get(token, "/user")


def get_teams(token: str) -> list[dict[str, Any]]:
    data = _get(token, "/team")
    teams = data.get("teams")
    if isinstance(teams, list):
        return [x for x in teams if isinstance(x, dict)]
    return []


def get_list_tasks(token: str, list_id: str, *, archived: bool = False) -> list[dict[str, Any]]:
    data = _get(token, f"/list/{list_id}/task", params={"archived": str(archived).lower()})
    tasks = data.get("tasks")
    if isinstance(tasks, list):
        return [x for x in tasks if isinstance(x, dict)]
    return []
