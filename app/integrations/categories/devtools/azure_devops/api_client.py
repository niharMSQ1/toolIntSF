"""Azure DevOps REST client: PAT Basic auth, api-version query, continuation pagination."""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.categories.devtools.azure_devops.credentials import basic_auth_header


def _log(r: httpx.Response) -> None:
    if os.environ.get("AZURE_DEVOPS_DEBUG_HTTP"):
        print(r.status_code, (r.text or "")[:1200])


def _headers(pat: str) -> dict[str, str]:
    return {
        "Authorization": basic_auth_header(pat),
        "Content-Type": "application/json",
    }


def _with_version(params: dict[str, Any], api_version: str) -> dict[str, Any]:
    p = dict(params)
    p.setdefault("api-version", api_version)
    return p


def request_json(
    method: str,
    url: str,
    pat: str,
    *,
    params: dict[str, Any] | None = None,
    api_version: str,
    timeout: float = 120.0,
    max_retries: int = 2,
) -> Any:
    q = _with_version(dict(params or {}), api_version)
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=timeout) as client:
            r = client.request(method, url, headers=_headers(pat), params=q)
            _log(r)
            if r.status_code == 429 and attempt < max_retries:
                ra = r.headers.get("Retry-After")
                try:
                    wait = float(ra) if ra else 2.0
                except ValueError:
                    wait = 2.0
                time.sleep(min(wait, 60.0))
                continue
            r.raise_for_status()
            if not (r.text or "").strip():
                return {}
            return r.json()
    return {}


def get_json(
    url: str,
    pat: str,
    *,
    params: dict[str, Any] | None = None,
    api_version: str,
) -> Any:
    return request_json("GET", url, pat, params=params, api_version=api_version)


def get_json_paginated(
    first_url: str,
    pat: str,
    *,
    api_version: str,
    list_key: str,
    max_items: int = 100,
    max_rounds: int = 25,
    initial_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Follow ``x-ms-continuationtoken`` / body continuationToken for list resources.
    See: https://learn.microsoft.com/en-us/azure/devops/integrate/how-to/call-rest-api
    """
    base_params = dict(initial_params or {})
    out: list[dict[str, Any]] = []
    url: str | None = first_url
    params: dict[str, Any] = dict(base_params)
    rounds = 0
    while url and len(out) < max_items and rounds < max_rounds:
        q = _with_version(dict(params), api_version)
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(pat), params=q)
            _log(r)
            r.raise_for_status()
            body = r.json() if (r.text or "").strip() else {}
        cont = r.headers.get("x-ms-continuationtoken") or (
            body.get("continuationToken") if isinstance(body, dict) else None
        )
        values = body.get(list_key) if isinstance(body, dict) else None
        if isinstance(values, list):
            for item in values:
                if isinstance(item, dict):
                    out.append(item)
                    if len(out) >= max_items:
                        return out[:max_items]
        if not cont:
            break
        params = {**base_params, "continuationToken": str(cont)}
        rounds += 1
    return out[:max_items]


def get_connection_data(base_url: str, organization: str, pat: str, *, api_version: str) -> dict[str, Any]:
    url = f"{base_url}/{quote(organization, safe='')}/_apis/connectionData"
    return get_json(url, pat, api_version=api_version)


def list_projects(base_url: str, organization: str, pat: str, *, api_version: str, top: int = 100) -> list[dict[str, Any]]:
    url = f"{base_url}/{quote(organization, safe='')}/_apis/projects"
    body = get_json(url, pat, params={"$top": top}, api_version=api_version)
    if isinstance(body, dict) and isinstance(body.get("value"), list):
        return [x for x in body["value"] if isinstance(x, dict)]
    return []


def get_repository(
    base_url: str,
    organization: str,
    project: str,
    repo_id_or_name: str,
    pat: str,
    *,
    api_version: str,
) -> dict[str, Any]:
    enc_org = quote(organization, safe="")
    enc_proj = quote(project, safe="")
    enc_repo = quote(repo_id_or_name, safe="")
    url = f"{base_url}/{enc_org}/{enc_proj}/_apis/git/repositories/{enc_repo}"
    return get_json(url, pat, api_version=api_version)


def list_repositories(
    base_url: str,
    organization: str,
    project: str,
    pat: str,
    *,
    api_version: str,
    max_items: int = 100,
) -> list[dict[str, Any]]:
    enc_org = quote(organization, safe="")
    enc_proj = quote(project, safe="")
    url = f"{base_url}/{enc_org}/{enc_proj}/_apis/git/repositories"
    return get_json_paginated(url, pat, api_version=api_version, list_key="value", max_items=max_items)


def list_commits(
    base_url: str,
    organization: str,
    project: str,
    repo_id: str,
    pat: str,
    *,
    api_version: str,
    max_items: int = 50,
) -> list[dict[str, Any]]:
    enc_org = quote(organization, safe="")
    enc_proj = quote(project, safe="")
    enc_repo = quote(repo_id, safe="")
    url = f"{base_url}/{enc_org}/{enc_proj}/_apis/git/repositories/{enc_repo}/commits"
    return get_json_paginated(url, pat, api_version=api_version, list_key="value", max_items=max_items)


def list_refs_heads(
    base_url: str,
    organization: str,
    project: str,
    repo_id: str,
    pat: str,
    *,
    api_version: str,
    max_items: int = 100,
) -> list[dict[str, Any]]:
    enc_org = quote(organization, safe="")
    enc_proj = quote(project, safe="")
    enc_repo = quote(repo_id, safe="")
    url = f"{base_url}/{enc_org}/{enc_proj}/_apis/git/repositories/{enc_repo}/refs"
    return get_json_paginated(
        url,
        pat,
        api_version=api_version,
        initial_params={"filter": "heads/"},
        list_key="value",
        max_items=max_items,
    )


def list_pull_requests(
    base_url: str,
    organization: str,
    project: str,
    pat: str,
    *,
    api_version: str,
    max_items: int = 50,
) -> list[dict[str, Any]]:
    enc_org = quote(organization, safe="")
    enc_proj = quote(project, safe="")
    url = f"{base_url}/{enc_org}/{enc_proj}/_apis/git/pullrequests"
    return get_json_paginated(url, pat, api_version=api_version, list_key="value", max_items=max_items)


def list_builds(
    base_url: str,
    organization: str,
    project: str,
    pat: str,
    *,
    api_version: str,
    max_items: int = 30,
) -> list[dict[str, Any]]:
    enc_org = quote(organization, safe="")
    enc_proj = quote(project, safe="")
    url = f"{base_url}/{enc_org}/{enc_proj}/_apis/build/builds"
    return get_json_paginated(url, pat, api_version=api_version, list_key="value", max_items=max_items)


def get_build_timeline(
    base_url: str,
    organization: str,
    project: str,
    build_id: int | str,
    pat: str,
    *,
    api_version: str,
) -> dict[str, Any]:
    enc_org = quote(organization, safe="")
    enc_proj = quote(project, safe="")
    url = f"{base_url}/{enc_org}/{enc_proj}/_apis/build/builds/{build_id}/timeline"
    return get_json(url, pat, api_version=api_version)


def list_build_artifacts(
    base_url: str,
    organization: str,
    project: str,
    build_id: int | str,
    pat: str,
    *,
    api_version: str,
) -> list[dict[str, Any]]:
    enc_org = quote(organization, safe="")
    enc_proj = quote(project, safe="")
    url = f"{base_url}/{enc_org}/{enc_proj}/_apis/build/builds/{build_id}/artifacts"
    body = get_json(url, pat, api_version=api_version)
    if isinstance(body, dict) and isinstance(body.get("value"), list):
        return [x for x in body["value"] if isinstance(x, dict)]
    return []
