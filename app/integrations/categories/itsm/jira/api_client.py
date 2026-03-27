"""Jira Cloud REST API via Atlassian OAuth (3LO)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.integrations.categories.itsm.jira.constants import ATLASSIAN_API_BASE


def list_accessible_resources(access_token: str) -> list[dict[str, Any]]:
    """GET /oauth/token/accessible-resources — returns cloud sites for the token."""
    url = f"{ATLASSIAN_API_BASE}/oauth/token/accessible-resources"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    with httpx.Client(timeout=60.0) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def pick_jira_cloud_id(resources: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    """Return (cloud_id, site_url) for the first Jira-looking site."""
    for r in resources:
        url = str(r.get("url") or "")
        rid = r.get("id")
        if rid and (".atlassian.net" in url or "jira" in url.lower() or r.get("name")):
            return str(rid), url or None
    if resources and resources[0].get("id"):
        r0 = resources[0]
        return str(r0["id"]), str(r0.get("url") or "")
    return None, None


def search_issues(
    cloud_id: str,
    access_token: str,
    jql: str,
    *,
    max_results_per_page: int = 50,
    max_issues_total: int = 200,
) -> dict[str, Any]:
    """POST /ex/jira/{cloudId}/rest/api/3/search"""
    url = f"{ATLASSIAN_API_BASE}/ex/jira/{cloud_id}/rest/api/3/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    all_issues: list[dict[str, Any]] = []
    start_at = 0
    total = None
    with httpx.Client(timeout=120.0) as client:
        while len(all_issues) < max_issues_total:
            body = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": min(max_results_per_page, max_issues_total - len(all_issues)),
                "fields": [
                    "summary",
                    "status",
                    "issuetype",
                    "created",
                    "updated",
                    "labels",
                    "priority",
                    "project",
                ],
            }
            r = client.post(url, headers=headers, content=json.dumps(body))
            r.raise_for_status()
            payload = r.json()
            if not isinstance(payload, dict):
                break
            issues = payload.get("issues")
            if not isinstance(issues, list):
                break
            for it in issues:
                if isinstance(it, dict):
                    all_issues.append(it)
            total = payload.get("total")
            if not issues:
                break
            start_at += len(issues)
            if total is not None and start_at >= int(total):
                break
            if len(issues) < body["maxResults"]:
                break

    return {
        "jql": jql,
        "total_hint": total,
        "issues_returned": len(all_issues),
        "issues": all_issues[:max_issues_total],
    }
