"""Snyk REST API (v2024) and v1 org listing — httpx."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integrations.categories.cspm.snyk.constants import (
    MAX_ISSUES_PER_SCOPE,
    MAX_PROJECTS_PER_ORG,
    SNYK_REST_API_VERSION,
)
from app.integrations.categories.cspm.snyk.credentials import rest_authorization_header
from app.integrations.categories.cspm.snyk.regions import resolve_rest_base_url, resolve_v1_base_url


class SnykApiError(RuntimeError):
    """Raised when Snyk returns an error response."""


def _rest_headers(cfg: dict[str, Any]) -> dict[str, str]:
    return {
        "Authorization": rest_authorization_header(cfg),
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "SNYK-API-Version": SNYK_REST_API_VERSION,
    }


def _v1_headers(cfg: dict[str, Any]) -> dict[str, str]:
    return {
        "Authorization": rest_authorization_header(cfg),
        "Content-Type": "application/json",
    }


def _region(cfg: dict[str, Any]) -> str | None:
    r = cfg.get("region")
    return str(r).strip() if r is not None and str(r).strip() else None


def _raise_for_snyk(resp: httpx.Response, what: str) -> None:
    if resp.status_code < 400:
        return
    body = resp.text[:2000]
    if resp.status_code in (401, 403):
        raise SnykApiError(
            f"Snyk authentication failed ({resp.status_code}) for {what}. "
            "Check API token / OAuth client credentials and org or group scope."
        )
    raise SnykApiError(f"Snyk API error {resp.status_code} for {what}: {body}")


def list_orgs_v1(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """GET /v1/orgs — returns org id, name, slug, etc."""
    region = _region(cfg)
    base = resolve_v1_base_url(region)
    url = f"{base}/orgs"
    with httpx.Client(timeout=60.0) as client:
        r = client.get(url, headers=_v1_headers(cfg))
        _raise_for_snyk(r, "GET /v1/orgs")
        data = r.json()
    orgs = data.get("orgs")
    if isinstance(orgs, list):
        return orgs
    return []


def validate_snyk_connection(cfg: dict[str, Any]) -> None:
    """Lightweight check: list orgs (requires a valid token with org access)."""
    list_orgs_v1(cfg)


def _paginate_rest(
    client: httpx.Client,
    headers: dict[str, str],
    first_url: str,
    *,
    max_items: int,
    label: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    url: str | None = first_url
    while url and len(out) < max_items:
        r = client.get(url, headers=headers)
        _raise_for_snyk(r, label)
        payload = r.json()
        if not isinstance(payload, dict):
            break
        chunk = payload.get("data")
        if isinstance(chunk, list):
            for item in chunk:
                if len(out) >= max_items:
                    break
                if isinstance(item, dict):
                    out.append(item)
        links = payload.get("links")
        if isinstance(links, dict):
            nxt = links.get("next")
            if nxt:
                nxt_s = str(nxt).strip()
                url = nxt_s if nxt_s.startswith("http") else urljoin(url, nxt_s)
            else:
                url = None
        else:
            url = None
    return out


def list_projects_for_org(
    cfg: dict[str, Any],
    org_id: str,
    *,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    cap = max_items if max_items is not None else MAX_PROJECTS_PER_ORG
    region = _region(cfg)
    rest = resolve_rest_base_url(region)
    first = f"{rest}/orgs/{org_id}/projects"
    with httpx.Client(timeout=120.0) as client:
        return _paginate_rest(
            client,
            _rest_headers(cfg),
            first,
            max_items=cap,
            label=f"GET projects org={org_id}",
        )


def list_issues_for_org(
    cfg: dict[str, Any],
    org_id: str,
    *,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    cap = max_items if max_items is not None else MAX_ISSUES_PER_SCOPE
    region = _region(cfg)
    rest = resolve_rest_base_url(region)
    first = f"{rest}/orgs/{org_id}/issues"
    with httpx.Client(timeout=120.0) as client:
        return _paginate_rest(
            client,
            _rest_headers(cfg),
            first,
            max_items=cap,
            label=f"GET issues org={org_id}",
        )


def list_issues_for_group(
    cfg: dict[str, Any],
    group_id: str,
    *,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    cap = max_items if max_items is not None else MAX_ISSUES_PER_SCOPE
    region = _region(cfg)
    rest = resolve_rest_base_url(region)
    first = f"{rest}/groups/{group_id}/issues"
    with httpx.Client(timeout=120.0) as client:
        return _paginate_rest(
            client,
            _rest_headers(cfg),
            first,
            max_items=cap,
            label=f"GET issues group={group_id}",
        )


def issue_attributes(issue: dict[str, Any]) -> dict[str, Any]:
    raw = issue.get("attributes")
    return raw if isinstance(raw, dict) else {}


def issue_type_hint(attrs: dict[str, Any]) -> str:
    """Lowercase type string for filtering (Snyk varies by product)."""
    for key in ("type", "issue_type", "problems", "title"):
        v = attrs.get(key)
        if v is None:
            continue
        if isinstance(v, (dict, list)):
            return json.dumps(v).lower()
        return str(v).lower()
    return json.dumps(attrs).lower()


def is_dependency_style_issue(attrs: dict[str, Any]) -> bool:
    h = issue_type_hint(attrs)
    if any(x in h for x in ("package", "sca", "license", "open source", "opensource", "container")):
        return True
    if "vulnerability" in h and "code" not in h and "sast" not in h:
        return True
    return False


def is_code_style_issue(attrs: dict[str, Any]) -> bool:
    h = issue_type_hint(attrs)
    return any(x in h for x in ("code", "sast", "static analysis", "snyk code"))


def summarize_severity(issues: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in issues:
        attrs = issue_attributes(item)
        sev = attrs.get("effective_severity_level") or attrs.get("severity") or "unknown"
        key = str(sev).lower() if sev is not None else "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def remediation_subset(issues: list[dict[str, Any]], limit: int = 500) -> list[dict[str, Any]]:
    """Trim issue payloads for storage: id, status, fix, severity."""
    rows: list[dict[str, Any]] = []
    for item in issues[:limit]:
        if not isinstance(item, dict):
            continue
        iid = item.get("id")
        attrs = issue_attributes(item)
        rows.append(
            {
                "id": iid,
                "effective_severity_level": attrs.get("effective_severity_level") or attrs.get("severity"),
                "status": attrs.get("status"),
                "ignored": attrs.get("ignored"),
                "fix_info": attrs.get("fix_info") or attrs.get("remediation"),
                "title": (attrs.get("title") or "")[:500],
            }
        )
    return rows
