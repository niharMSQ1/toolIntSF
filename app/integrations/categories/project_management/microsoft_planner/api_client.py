"""Microsoft Graph REST — Planner resources."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.integrations.categories.project_management.microsoft_planner.constants import GRAPH_API_BASE

_MAX_RETRIES = 6


def _request(
    method: str,
    access_token: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = path if path.startswith("http") else f"{GRAPH_API_BASE}{path}"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    last: httpx.Response | None = None
    for _ in range(_MAX_RETRIES):
        with httpx.Client(timeout=120.0) as client:
            if json_body is not None:
                headers["Content-Type"] = "application/json"
                r = client.request(method, url, headers=headers, params=params, content=json.dumps(json_body))
            else:
                r = client.request(method, url, headers=headers, params=params)
        last = r
        if r.status_code == 429:
            ra = r.headers.get("Retry-After")
            try:
                time.sleep(min(float(ra) if ra else 2.0, 60.0))
            except ValueError:
                time.sleep(2.0)
            continue
        r.raise_for_status()
        if r.status_code == 204 or not r.content:
            return {}
        return r.json()
    if last is not None:
        last.raise_for_status()
    raise RuntimeError("Graph request failed")


def get_me(access_token: str) -> dict[str, Any]:
    return _request("GET", access_token, "/me")


def list_plans_for_group(access_token: str, group_id: str) -> list[dict[str, Any]]:
    """GET /groups/{id}/planner/plans — https://learn.microsoft.com/en-us/graph/api/plannerplan-list"""
    data = _request("GET", access_token, f"/groups/{group_id}/planner/plans")
    val = data.get("value")
    if isinstance(val, list):
        return [x for x in val if isinstance(x, dict)]
    return []


def list_tasks_for_plan(access_token: str, plan_id: str) -> list[dict[str, Any]]:
    """GET /planner/plans/{id}/tasks — https://learn.microsoft.com/en-us/graph/api/plannertask-list-plan-tasks"""
    data = _request("GET", access_token, f"/planner/plans/{plan_id}/tasks")
    val = data.get("value")
    if isinstance(val, list):
        return [x for x in val if isinstance(x, dict)]
    return []


def get_plan(access_token: str, plan_id: str) -> dict[str, Any]:
    return _request("GET", access_token, f"/planner/plans/{plan_id}")
