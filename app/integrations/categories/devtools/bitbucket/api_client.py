"""Low-level Bitbucket Cloud 2.0 REST helpers with pagination caps."""

from __future__ import annotations

import os
from typing import Any

import httpx

from app.integrations.categories.devtools.bitbucket.constants import BITBUCKET_API_BASE


def _log(r: httpx.Response) -> None:
    if os.environ.get("BITBUCKET_DEBUG_HTTP"):
        print(r.status_code, r.text[:1500])


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def get_json(url: str, token: str, *, params: dict[str, Any] | None = None, timeout: float = 120.0) -> dict[str, Any]:
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=_headers(token), params=params or {})
        _log(r)
        r.raise_for_status()
        return r.json()


def paginate_values(
    first_url: str,
    token: str,
    *,
    params: dict[str, Any] | None = None,
    max_pages: int = 20,
) -> list[dict[str, Any]]:
    """Follow ``next`` links and concatenate ``values`` (capped by ``max_pages``)."""
    out: list[dict[str, Any]] = []
    url: str | None = first_url
    first_params = dict(params or {})
    first_params.setdefault("pagelen", 50)
    pages = 0
    with httpx.Client(timeout=120.0) as client:
        while url and pages < max_pages:
            if pages == 0:
                r = client.get(url, headers=_headers(token), params=first_params)
            else:
                r = client.get(url, headers=_headers(token))
            _log(r)
            r.raise_for_status()
            body = r.json()
            for v in body.get("values") or []:
                if isinstance(v, dict):
                    out.append(v)
            nxt = body.get("next")
            url = nxt if isinstance(nxt, str) and nxt.strip() else None
            pages += 1
    return out


def list_repositories(workspace: str, token: str, *, max_repos: int = 40) -> list[dict[str, Any]]:
    url = f"{BITBUCKET_API_BASE}/repositories/{workspace}"
    rows = paginate_values(url, token, params={"pagelen": 100}, max_pages=10)
    return rows[:max_repos]


def list_commits(workspace: str, repo_slug: str, token: str, *, limit: int = 30) -> list[dict[str, Any]]:
    url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/commits/"
    vals = paginate_values(url, token, params={"pagelen": min(100, limit)}, max_pages=2)
    return vals[:limit]


def list_pull_requests(
    workspace: str,
    repo_slug: str,
    token: str,
    *,
    state: str | None = None,
    max_prs: int = 50,
) -> list[dict[str, Any]]:
    url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/pullrequests"
    params: dict[str, Any] = {"pagelen": min(50, max_prs)}
    if state:
        params["state"] = state
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url, headers=_headers(token), params=params)
        _log(r)
        r.raise_for_status()
        body = r.json()
        vals = [v for v in (body.get("values") or []) if isinstance(v, dict)]
        return vals[:max_prs]


def list_pipeline_runs(workspace: str, repo_slug: str, token: str, *, max_runs: int = 30) -> list[dict[str, Any]]:
    url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/pipelines/"
    vals = paginate_values(url, token, params={"pagelen": 30}, max_pages=5)
    return vals[:max_runs]


def list_deployments(workspace: str, repo_slug: str, token: str, *, max_items: int = 40) -> list[dict[str, Any]]:
    url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/deployments/"
    try:
        vals = paginate_values(url, token, params={"pagelen": 30}, max_pages=5)
        return vals[:max_items]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return []
        raise


def list_repo_hooks(workspace: str, repo_slug: str, token: str) -> list[dict[str, Any]]:
    url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/hooks"
    try:
        return paginate_values(url, token, max_pages=3, page_size=50)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (404, 403):
            return []
        raise


def list_branch_restrictions(workspace: str, repo_slug: str, token: str) -> list[dict[str, Any]]:
    url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/branch-restrictions"
    try:
        return paginate_values(url, token, max_pages=3, page_size=50)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (404, 403):
            return []
        raise


def list_issues(workspace: str, repo_slug: str, token: str, *, max_items: int = 30) -> list[dict[str, Any]]:
    url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/issues"
    try:
        vals = paginate_values(url, token, max_pages=3, page_size=30)
        return vals[:max_items]
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (404, 403):
            return []
        raise
