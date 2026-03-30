"""CircleCI API v2 client (Circle-Token header)."""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote

import httpx


def _log(r: httpx.Response) -> None:
    if os.environ.get("CIRCLECI_DEBUG_HTTP"):
        print(r.status_code, (r.text or "")[:1200])


def _headers(token: str) -> dict[str, str]:
    return {
        "Circle-Token": token,
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


def get_me(base_url: str, token: str) -> dict[str, Any]:
    return get_json(base_url, token, "/me")


def get_project(base_url: str, token: str, project_slug: str) -> dict[str, Any]:
    enc = quote(project_slug, safe="")
    return get_json(base_url, token, f"/project/{enc}")


def list_pipelines(
    base_url: str,
    token: str,
    project_slug: str,
    *,
    max_items: int = 30,
) -> list[dict[str, Any]]:
    enc = quote(project_slug, safe="")
    out: list[dict[str, Any]] = []
    next_token: str | None = None
    rounds = 0
    while len(out) < max_items and rounds < 20:
        q: dict[str, Any] = {}
        if next_token:
            q["page-token"] = next_token
        body = get_json(base_url, token, f"/project/{enc}/pipeline", params=q)
        items = body.get("items") if isinstance(body, dict) else None
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict):
                    out.append(it)
                    if len(out) >= max_items:
                        return out[:max_items]
        next_token = body.get("next_page_token") if isinstance(body, dict) else None
        if not next_token:
            break
        rounds += 1
    return out[:max_items]


def get_pipeline(base_url: str, token: str, pipeline_id: str) -> dict[str, Any]:
    return get_json(base_url, token, f"/pipeline/{quote(pipeline_id, safe='')}")


def get_workflow(base_url: str, token: str, workflow_id: str) -> dict[str, Any]:
    return get_json(base_url, token, f"/workflow/{quote(workflow_id, safe='')}")


def list_workflow_jobs(base_url: str, token: str, workflow_id: str) -> list[dict[str, Any]]:
    body = get_json(base_url, token, f"/workflow/{quote(workflow_id, safe='')}/job")
    items = body.get("items") if isinstance(body, dict) else None
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict)]


def validate_token(base_url: str, token: str) -> bool:
    try:
        get_me(base_url, token)
        return True
    except httpx.HTTPStatusError:
        return False
