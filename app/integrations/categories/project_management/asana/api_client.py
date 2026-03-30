"""Asana REST API client with 429 Retry-After handling — https://developers.asana.com/reference/rest-api-reference"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.integrations.categories.project_management.asana.constants import ASANA_API_BASE

_MAX_RETRIES = 8


def _sleep_for_retry(response: httpx.Response) -> float | None:
    if response.status_code != 429:
        return None
    ra = response.headers.get("Retry-After")
    if ra is None:
        return 1.0
    try:
        return float(ra)
    except ValueError:
        return 1.0


def request_json(
    method: str,
    token: str,
    path_or_url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Perform one logical request; retries on 429 using Retry-After (see rate limits doc).
    """
    url = path_or_url if path_or_url.startswith("http") else f"{ASANA_API_BASE}{path_or_url}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    last: httpx.Response | None = None
    for attempt in range(_MAX_RETRIES):
        with httpx.Client(timeout=120.0) as client:
            if json_body is not None:
                headers["Content-Type"] = "application/json"
                r = client.request(method, url, headers=headers, params=params, content=json.dumps(json_body))
            else:
                r = client.request(method, url, headers=headers, params=params)
        last = r
        if r.status_code != 429:
            r.raise_for_status()
            return r.json()
        delay = _sleep_for_retry(r)
        if delay is None:
            break
        time.sleep(min(delay, 120.0))
    if last is not None:
        last.raise_for_status()
    raise RuntimeError("Asana request failed without response")


def get_me(token: str) -> dict[str, Any]:
    return request_json("GET", token, "/users/me")


def list_workspaces(token: str) -> list[dict[str, Any]]:
    payload = request_json("GET", token, "/workspaces")
    data = payload.get("data")
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def list_projects_for_workspace(token: str, workspace_gid: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    params: dict[str, Any] = {
        "limit": 100,
        "opt_fields": "gid,name,archived,permalink_url",
    }
    url: str | None = f"/workspaces/{workspace_gid}/projects"
    while url:
        payload = request_json(
            "GET",
            token,
            url,
            params=params if not str(url).startswith("http") else None,
        )
        data = payload.get("data")
        if isinstance(data, list):
            out.extend([x for x in data if isinstance(x, dict)])
        nxt = payload.get("next_page")
        if isinstance(nxt, dict) and nxt.get("uri"):
            url = str(nxt["uri"])
            params = None
        else:
            url = None
    return out


def get_project(token: str, project_gid: str) -> dict[str, Any]:
    payload = request_json(
        "GET",
        token,
        f"/projects/{project_gid}",
        params={"opt_fields": "gid,name,archived,permalink_url"},
    )
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return {}


def list_tasks_for_project(
    token: str,
    project_gid: str,
    *,
    max_tasks: int = 500,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    opt = (
        "gid,name,completed,due_on,due_at,assignee,permalink_url,"
        "memberships,memberships.project,memberships.section"
    )
    params: dict[str, Any] = {
        "project": project_gid,
        "limit": 100,
        "opt_fields": opt,
    }
    url: str | None = "/tasks"
    while url and len(out) < max_tasks:
        payload = request_json(
            "GET",
            token,
            url,
            params=params if not str(url).startswith("http") else None,
        )
        data = payload.get("data")
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    out.append(row)
                    if len(out) >= max_tasks:
                        break
        nxt = payload.get("next_page")
        if isinstance(nxt, dict) and nxt.get("uri"):
            url = str(nxt["uri"])
            params = None
        else:
            url = None
    return out[:max_tasks]


def get_task(token: str, task_gid: str) -> dict[str, Any]:
    opt = (
        "gid,name,completed,due_on,due_at,assignee,permalink_url,"
        "memberships,memberships.project,memberships.section"
    )
    payload = request_json("GET", token, f"/tasks/{task_gid}", params={"opt_fields": opt})
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return {}


def get_user(token: str, user_gid: str) -> dict[str, Any]:
    payload = request_json(
        "GET",
        token,
        f"/users/{user_gid}",
        params={"opt_fields": "gid,name,email"},
    )
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return {}


def list_stories_for_task(token: str, task_gid: str, *, max_stories: int = 200) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    params: dict[str, Any] = {
        "task": task_gid,
        "limit": 100,
        "opt_fields": "gid,type,text,created_at,created_by,created_by.name",
    }
    url: str | None = "/stories"
    while url and len(out) < max_stories:
        payload = request_json(
            "GET",
            token,
            url,
            params=params if not str(url).startswith("http") else None,
        )
        data = payload.get("data")
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    out.append(row)
                    if len(out) >= max_stories:
                        break
        nxt = payload.get("next_page")
        if isinstance(nxt, dict) and nxt.get("uri"):
            url = str(nxt["uri"])
            params = None
        else:
            url = None
    return out[:max_stories]


def create_webhook(
    token: str,
    *,
    resource_gid: str,
    target_url: str,
    filters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """POST /webhooks — https://developers.asana.com/reference/createwebhook"""
    body: dict[str, Any] = {
        "data": {
            "resource": resource_gid,
            "target": target_url,
        }
    }
    if filters:
        body["data"]["filters"] = filters
    return request_json("POST", token, "/webhooks", json_body=body)
