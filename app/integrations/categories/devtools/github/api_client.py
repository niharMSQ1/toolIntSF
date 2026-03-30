"""GitHub REST API client — pagination via Link rel=next; 429 honors Retry-After."""

from __future__ import annotations

import os
import re
import time
from typing import Any

import httpx

from app.integrations.categories.devtools.github.constants import GITHUB_API_BASE, GITHUB_API_VERSION


def _log(r: httpx.Response) -> None:
    if os.environ.get("GITHUB_DEBUG_HTTP"):
        print(r.status_code, (r.text or "")[:1500])


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def _parse_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    m = re.search(r"<([^>]+)>;\s*rel=\"next\"", link_header)
    return m.group(1).strip() if m else None


def _request(
    method: str,
    url: str,
    token: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: float = 120.0,
    max_retries: int = 2,
) -> httpx.Response:
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=timeout) as client:
            kwargs: dict[str, Any] = {"headers": _headers(token), "params": params}
            if json_body is not None:
                kwargs["json"] = json_body
            r = client.request(method, url, **kwargs)
            _log(r)
            if r.status_code == 429 and attempt < max_retries:
                ra = r.headers.get("Retry-After")
                try:
                    wait = float(ra) if ra else 2.0
                except ValueError:
                    wait = 2.0
                time.sleep(min(wait, 60.0))
                continue
            return r
    raise RuntimeError("GitHub request failed after retries")


def get_json(
    url: str,
    token: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = 120.0,
) -> Any:
    r = _request("GET", url, token, params=params, timeout=timeout)
    r.raise_for_status()
    if not (r.text or "").strip():
        return {}
    return r.json()


def paginate_json_array(
    first_url: str,
    token: str,
    *,
    params: dict[str, Any] | None = None,
    max_items: int = 100,
    per_page: int = 30,
) -> list[dict[str, Any]]:
    """Concatenate JSON array pages following Link: ... rel=\"next\"."""
    out: list[dict[str, Any]] = []
    url: str | None = first_url
    first_params = dict(params or {})
    first_params.setdefault("per_page", min(per_page, 100))
    pages = 0
    max_pages = 20
    while url and len(out) < max_items and pages < max_pages:
        p = first_params if pages == 0 else None
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(token), params=p)
            _log(r)
            r.raise_for_status()
            body = r.json()
        if isinstance(body, list):
            for item in body:
                if isinstance(item, dict):
                    out.append(item)
                    if len(out) >= max_items:
                        break
        url = _parse_next_link(r.headers.get("Link"))
        pages += 1
        first_params = {}
    return out[:max_items]


def get_repository(owner: str, repo: str, token: str) -> dict[str, Any]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    return get_json(url, token)


def get_user(token: str) -> dict[str, Any]:
    return get_json(f"{GITHUB_API_BASE}/user", token)


def list_commits(owner: str, repo: str, token: str, *, max_items: int = 50) -> list[dict[str, Any]]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
    return paginate_json_array(url, token, max_items=max_items)


def list_branches(owner: str, repo: str, token: str, *, max_items: int = 50) -> list[dict[str, Any]]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches"
    return paginate_json_array(url, token, max_items=max_items)


def list_pull_requests(
    owner: str,
    repo: str,
    token: str,
    *,
    state: str = "open",
    max_items: int = 50,
) -> list[dict[str, Any]]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"
    return paginate_json_array(url, token, params={"state": state}, max_items=max_items)


def list_workflow_runs(owner: str, repo: str, token: str, *, max_items: int = 30) -> list[dict[str, Any]]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs"
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url, headers=_headers(token), params={"per_page": min(30, max_items)})
        _log(r)
        r.raise_for_status()
        body = r.json()
    runs = body.get("workflow_runs") if isinstance(body, dict) else None
    if not isinstance(runs, list):
        return []
    out = [x for x in runs if isinstance(x, dict)]
    return out[:max_items]


def list_jobs_for_run(owner: str, repo: str, run_id: int | str, token: str) -> list[dict[str, Any]]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url, headers=_headers(token), params={"per_page": 100})
        _log(r)
        r.raise_for_status()
        body = r.json()
    jobs = body.get("jobs") if isinstance(body, dict) else None
    if not isinstance(jobs, list):
        return []
    return [j for j in jobs if isinstance(j, dict)]


def list_artifacts(owner: str, repo: str, token: str, *, max_items: int = 30) -> list[dict[str, Any]]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/artifacts"
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url, headers=_headers(token), params={"per_page": min(30, max_items)})
        _log(r)
        r.raise_for_status()
        body = r.json()
    arts = body.get("artifacts") if isinstance(body, dict) else None
    if not isinstance(arts, list):
        return []
    out = [a for a in arts if isinstance(a, dict)]
    return out[:max_items]
