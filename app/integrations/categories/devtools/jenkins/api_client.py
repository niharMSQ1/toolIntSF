"""Jenkins JSON API client (HTTP Basic: user + API token)."""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote

import httpx


def _log(r: httpx.Response) -> None:
    if os.environ.get("JENKINS_DEBUG_HTTP"):
        print(r.status_code, (r.text or "")[:1200])


def _client(base_url: str, username: str, token: str, timeout: float = 120.0) -> httpx.Client:
    return httpx.Client(
        base_url=base_url,
        auth=(username, token),
        timeout=timeout,
        headers={"Accept": "application/json"},
    )


def job_path_url_segments(job_path: str) -> str:
    """Turn ``folder/my-job`` into ``job/folder/job/my-job`` for Jenkins URLs."""
    parts = [p for p in job_path.strip("/").split("/") if p]
    return "/".join(f"job/{quote(p, safe='')}" for p in parts)


def get_json(
    base_url: str,
    username: str,
    token: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    path = path if path.startswith("/") else f"/{path}"
    for attempt in range(max_retries + 1):
        with _client(base_url, username, token) as client:
            r = client.get(path, params=params or {})
            _log(r)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not (r.text or "").strip():
                return {}
            return r.json()
    return {}


def get_whoami(base_url: str, username: str, token: str) -> dict[str, Any]:
    try:
        return get_json(base_url, username, token, "/whoAmI/api/json")
    except httpx.HTTPStatusError:
        return get_json(base_url, username, token, f"/user/{quote(username, safe='')}/api/json")


def list_jobs(base_url: str, username: str, token: str, *, tree: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if tree:
        params["tree"] = tree
    else:
        params["tree"] = "jobs[name,url,fullName,_class]{0,200}"
    body = get_json(base_url, username, token, "/api/json", params=params)
    jobs = body.get("jobs") if isinstance(body, dict) else None
    if not isinstance(jobs, list):
        return []
    return [j for j in jobs if isinstance(j, dict)]


def list_builds_for_job(
    base_url: str,
    username: str,
    token: str,
    job_path: str,
    *,
    limit: int = 30,
) -> list[dict[str, Any]]:
    jp = job_path_url_segments(job_path)
    tree = f"builds[number,url,result,building,timestamp,duration,fullDisplayName]{{{0},{limit}}}"
    body = get_json(base_url, username, token, f"/{jp}/api/json", params={"tree": tree})
    builds = body.get("builds") if isinstance(body, dict) else None
    if not isinstance(builds, list):
        return []
    return [b for b in builds if isinstance(b, dict)]


def get_build(
    base_url: str,
    username: str,
    token: str,
    job_path: str,
    build_number: int | str,
) -> dict[str, Any]:
    jp = job_path_url_segments(job_path)
    return get_json(base_url, username, token, f"/{jp}/{build_number}/api/json")


def get_wfapi_describe(
    base_url: str,
    username: str,
    token: str,
    job_path: str,
    build_number: int | str,
) -> dict[str, Any]:
    jp = job_path_url_segments(job_path)
    return get_json(base_url, username, token, f"/{jp}/{build_number}/wfapi/describe")


def validate_connection(base_url: str, username: str, token: str) -> bool:
    try:
        get_json(base_url, username, token, "/api/json", params={"tree": "mode"})
        return True
    except httpx.HTTPStatusError:
        return False
