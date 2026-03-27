"""Wiz GraphQL API (Issues, graph resources, vulnerability findings, users)."""

from __future__ import annotations

import json
from typing import Any

import httpx

# GraphQL field names vary slightly across Wiz tenant versions; we try multiple shapes.

_ISSUES_NODES = """
query IssuesNodes($first: Int!, $after: String) {
  issues(first: $first, after: $after) {
    nodes {
      id
      name
      severity
      status
      createdAt
      updatedAt
      type
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_ISSUES_EDGES = """
query IssuesEdges($first: Int!, $after: String) {
  issues(first: $first, after: $after) {
    edges {
      node {
        id
        name
        severity
        status
        createdAt
        updatedAt
        type
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_VULN_NODES = """
query VulnNodes($first: Int!, $after: String) {
  vulnerabilityFindings(first: $first, after: $after) {
    nodes {
      id
      name
      severity
      status
      createdAt
      updatedAt
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_CLOUD_RESOURCES = """
query CloudResources($first: Int!, $after: String) {
  cloudResources(first: $first, after: $after) {
    nodes {
      id
      name
      nativeType
      type
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_PROJECTS = """
query Projects($first: Int!, $after: String) {
  projects(first: $first, after: $after) {
    nodes {
      id
      name
      slug
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_USERS = """
query UsersWiz($first: Int!, $after: String) {
  users(first: $first, after: $after) {
    nodes {
      id
      name
      email
      isActive
      createdAt
      lastLoginAt
      role { name }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


def graphql_post(
    graphql_url: str,
    access_token: str,
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {"query": query}
    if variables:
        body["variables"] = variables
    with httpx.Client(timeout=timeout_sec) as client:
        r = client.post(graphql_url, headers=headers, content=json.dumps(body))
        r.raise_for_status()
        out = r.json()
    if not isinstance(out, dict):
        raise ValueError("Invalid GraphQL response")
    return out


def paginate_issues(
    graphql_url: str,
    access_token: str,
    *,
    max_pages: int = 5,
    page_size: int = 100,
) -> dict[str, Any]:
    """Fetch issues using nodes or edges query shape."""
    last_errors: list[Any] = []
    for shape_name, q in (("nodes", _ISSUES_NODES), ("edges", _ISSUES_EDGES)):
        all_items: list[dict[str, Any]] = []
        after: str | None = None
        last_page: dict[str, Any] = {}
        for _ in range(max_pages):
            payload = graphql_post(
                graphql_url,
                access_token,
                q,
                {"first": min(page_size, 500), "after": after},
            )
            if payload.get("errors"):
                last_errors = list(payload["errors"])
                break
            data = payload.get("data") or {}
            issues = data.get("issues") if isinstance(data, dict) else None
            if not isinstance(issues, dict):
                last_errors = [{"message": "issues field missing in GraphQL data"}]
                break
            used_nodes = False
            nodes = issues.get("nodes")
            if isinstance(nodes, list):
                used_nodes = True
                for n in nodes:
                    if isinstance(n, dict):
                        all_items.append(n)
            else:
                edges = issues.get("edges")
                if isinstance(edges, list):
                    for e in edges:
                        if isinstance(e, dict) and isinstance(e.get("node"), dict):
                            all_items.append(e["node"])
            pi = issues.get("pageInfo") if isinstance(issues.get("pageInfo"), dict) else {}
            last_page = pi
            if not pi.get("hasNextPage") or not pi.get("endCursor"):
                return {
                    "query_shape": shape_name if used_nodes else "edges",
                    "issues_sampled_count": len(all_items),
                    "issues": all_items[: min(len(all_items), 2000)],
                    "page_info": last_page,
                    "graphql_errors": None,
                }
            after = str(pi.get("endCursor"))
        if all_items:
            return {
                "query_shape": shape_name,
                "issues_sampled_count": len(all_items),
                "issues": all_items[: min(len(all_items), 2000)],
                "page_info": last_page,
                "graphql_errors": None,
            }
    return {
        "query_shape": None,
        "issues_sampled_count": 0,
        "issues": [],
        "page_info": {},
        "graphql_errors": last_errors
        or [{"message": "Could not query issues; verify API scopes (read:issues) and GraphQL endpoint."}],
    }


def paginate_issues_critical_high(
    graphql_url: str,
    access_token: str,
    *,
    max_pages: int = 5,
    page_size: int = 100,
) -> dict[str, Any]:
    base = paginate_issues(graphql_url, access_token, max_pages=max_pages, page_size=page_size)
    high = []
    for it in base.get("issues") or []:
        if not isinstance(it, dict):
            continue
        sev = str(it.get("severity") or "").upper()
        if sev in ("CRITICAL", "HIGH"):
            high.append(it)
    base["severity_filter"] = ["CRITICAL", "HIGH"]
    base["issues_matching_severity"] = high[: min(len(high), 2000)]
    return base


def paginate_vulnerability_findings(
    graphql_url: str,
    access_token: str,
    *,
    max_pages: int = 4,
    page_size: int = 100,
) -> dict[str, Any]:
    all_items: list[dict[str, Any]] = []
    after: str | None = None
    last_page: dict[str, Any] = {}
    errors: list[Any] = []

    for _ in range(max_pages):
        payload = graphql_post(
            graphql_url,
            access_token,
            _VULN_NODES,
            {"first": min(page_size, 500), "after": after},
        )
        if payload.get("errors"):
            errors.extend(payload["errors"])
            break
        data = payload.get("data") or {}
        vf = data.get("vulnerabilityFindings") if isinstance(data, dict) else None
        if not isinstance(vf, dict):
            errors.append({"message": "vulnerabilityFindings query not available or no scopes."})
            break
        nodes = vf.get("nodes")
        if isinstance(nodes, list):
            for n in nodes:
                if isinstance(n, dict):
                    all_items.append(n)
        pi = vf.get("pageInfo") if isinstance(vf.get("pageInfo"), dict) else {}
        last_page = pi
        if not pi.get("hasNextPage") or not pi.get("endCursor"):
            break
        after = str(pi.get("endCursor"))

    return {
        "vulnerability_findings_count": len(all_items),
        "vulnerability_findings": all_items[: min(len(all_items), 2000)],
        "page_info": last_page,
        "graphql_errors": errors or None,
    }


def fetch_cloud_inventory_and_projects(
    graphql_url: str,
    access_token: str,
    *,
    max_pages: int = 3,
) -> dict[str, Any]:
    """Projects + cloud resources (best-effort; requires graph scopes)."""
    resources: list[dict[str, Any]] = []
    projects: list[dict[str, Any]] = []
    errors: list[Any] = []

    after_r: str | None = None
    for _ in range(max_pages):
        payload = graphql_post(
            graphql_url,
            access_token,
            _CLOUD_RESOURCES,
            {"first": 200, "after": after_r},
        )
        if payload.get("errors"):
            errors.extend(payload["errors"])
            break
        data = payload.get("data") or {}
        cr = data.get("cloudResources") if isinstance(data, dict) else None
        if not isinstance(cr, dict):
            break
        nodes = cr.get("nodes")
        if isinstance(nodes, list):
            for n in nodes:
                if isinstance(n, dict):
                    resources.append(n)
        pi = cr.get("pageInfo") if isinstance(cr.get("pageInfo"), dict) else {}
        if not pi.get("hasNextPage") or not pi.get("endCursor"):
            break
        after_r = str(pi.get("endCursor"))

    after_p: str | None = None
    for _ in range(max_pages):
        payload = graphql_post(
            graphql_url,
            access_token,
            _PROJECTS,
            {"first": 100, "after": after_p},
        )
        if payload.get("errors"):
            errors.extend(payload["errors"])
            break
        data = payload.get("data") or {}
        pr = data.get("projects") if isinstance(data, dict) else None
        if not isinstance(pr, dict):
            break
        nodes = pr.get("nodes")
        if isinstance(nodes, list):
            for n in nodes:
                if isinstance(n, dict):
                    projects.append(n)
        pi = pr.get("pageInfo") if isinstance(pr.get("pageInfo"), dict) else {}
        if not pi.get("hasNextPage") or not pi.get("endCursor"):
            break
        after_p = str(pi.get("endCursor"))

    return {
        "cloud_resources_count": len(resources),
        "cloud_resources_sample": resources[:2000],
        "projects_count": len(projects),
        "projects": projects[:500],
        "graphql_errors": errors or None,
    }


def fetch_users_sample(graphql_url: str, access_token: str, *, max_pages: int = 2) -> dict[str, Any]:
    users: list[dict[str, Any]] = []
    errors: list[Any] = []
    after: str | None = None
    for _ in range(max_pages):
        payload = graphql_post(
            graphql_url,
            access_token,
            _USERS,
            {"first": 200, "after": after},
        )
        if payload.get("errors"):
            errors.extend(payload["errors"])
            break
        data = payload.get("data") or {}
        u = data.get("users") if isinstance(data, dict) else None
        if not isinstance(u, dict):
            return {"users": [], "graphql_errors": errors or [{"message": "users query failed"}]}
        nodes = u.get("nodes")
        if isinstance(nodes, list):
            for n in nodes:
                if isinstance(n, dict):
                    users.append(n)
        pi = u.get("pageInfo") if isinstance(u.get("pageInfo"), dict) else {}
        if not pi.get("hasNextPage") or not pi.get("endCursor"):
            break
        after = str(pi.get("endCursor"))

    return {
        "users_count": len(users),
        "users": users[:2000],
        "note": "Wiz portal audit logs for admin actions may require export from Wiz; API lists users and last login.",
        "graphql_errors": errors or None,
    }
