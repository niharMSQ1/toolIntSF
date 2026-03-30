"""Linear GraphQL — Authorization: <Personal API Key> — https://developers.linear.app/docs/graphql/working-with-the-graphql-api"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.integrations.categories.project_management.linear.constants import LINEAR_API_URL

_MAX = 6


def graphql(api_key: str, query: str, *, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"Authorization": api_key, "Content-Type": "application/json", "Accept": "application/json"}
    body: dict[str, Any] = {"query": query}
    if variables:
        body["variables"] = variables
    last: httpx.Response | None = None
    for _ in range(_MAX):
        with httpx.Client(timeout=120.0) as client:
            r = client.post(LINEAR_API_URL, headers=headers, content=json.dumps(body))
        last = r
        if r.status_code == 429:
            time.sleep(2.0)
            continue
        r.raise_for_status()
        return r.json()
    if last:
        last.raise_for_status()
    raise RuntimeError("Linear GraphQL failed")


def graphql_data(api_key: str, query: str, *, variables: dict[str, Any] | None = None) -> dict[str, Any] | None:
    payload = graphql(api_key, query, variables=variables)
    err = payload.get("errors")
    if isinstance(err, list) and err:
        first = err[0] if err else {}
        msg = first.get("message") if isinstance(first, dict) else str(err)
        raise ValueError(f"Linear GraphQL error: {msg}")
    data = payload.get("data")
    return data if isinstance(data, dict) else None


def get_viewer(api_key: str) -> dict[str, Any]:
    q = "query { viewer { id name email } }"
    data = graphql_data(api_key, q)
    return (data or {}).get("viewer") if data else {}


def list_issues(api_key: str, *, first: int = 50) -> list[dict[str, Any]]:
    q = """
    query ($first: Int!) {
      issues(first: $first) {
        nodes {
          id
          identifier
          title
          state { name }
          url
        }
      }
    }
    """
    data = graphql_data(api_key, q, variables={"first": min(first, 100)})
    issues = (data or {}).get("issues") if data else None
    if isinstance(issues, dict):
        nodes = issues.get("nodes")
        if isinstance(nodes, list):
            return [x for x in nodes if isinstance(x, dict)]
    return []


def list_projects(api_key: str, *, first: int = 50) -> list[dict[str, Any]]:
    q = """
    query ($first: Int!) {
      projects(first: $first) {
        nodes {
          id
          name
          url
        }
      }
    }
    """
    data = graphql_data(api_key, q, variables={"first": min(first, 100)})
    proj = (data or {}).get("projects") if data else None
    if isinstance(proj, dict):
        nodes = proj.get("nodes")
        if isinstance(nodes, list):
            return [x for x in nodes if isinstance(x, dict)]
    return []
