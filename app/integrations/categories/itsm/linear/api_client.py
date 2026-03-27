"""Linear GraphQL API client."""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.itsm.linear.constants import LINEAR_GRAPHQL_URL


def _graphql_request(
    access_token: str,
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    graphql_url: str = LINEAR_GRAPHQL_URL,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {"query": query, "variables": variables or {}}
    with httpx.Client(timeout=60.0) as client:
        r = client.post(graphql_url, json=body, headers=headers)
        r.raise_for_status()
        payload = r.json()
    if not isinstance(payload, dict):
        raise ValueError("Linear GraphQL response was not a JSON object.")
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        messages = [str(err.get("message") or "GraphQL error") for err in errors if isinstance(err, dict)]
        raise ValueError("; ".join(messages) if messages else "Linear GraphQL request failed.")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Linear GraphQL response missing data.")
    return data


def _issue_fields() -> str:
    return """
        id
        identifier
        title
        description
        url
        priority
        createdAt
        updatedAt
        team { id key name }
        project { id name }
        state { id name }
    """


def get_teams(access_token: str, *, graphql_url: str = LINEAR_GRAPHQL_URL, first: int = 100) -> list[dict[str, Any]]:
    query = """
    query GetTeams($first: Int!) {
      teams(first: $first) {
        nodes {
          id
          key
          name
          description
          private
          archivedAt
        }
      }
    }
    """
    data = _graphql_request(access_token, query, {"first": first}, graphql_url=graphql_url)
    teams = data.get("teams")
    if not isinstance(teams, dict):
        return []
    nodes = teams.get("nodes")
    if not isinstance(nodes, list):
        return []
    return [node for node in nodes if isinstance(node, dict)]


def get_projects(access_token: str, *, graphql_url: str = LINEAR_GRAPHQL_URL, first: int = 100) -> list[dict[str, Any]]:
    query = """
    query GetProjects($first: Int!) {
      projects(first: $first) {
        nodes {
          id
          name
          description
          progress
          targetDate
          state
        }
      }
    }
    """
    data = _graphql_request(access_token, query, {"first": first}, graphql_url=graphql_url)
    projects = data.get("projects")
    if not isinstance(projects, dict):
        return []
    nodes = projects.get("nodes")
    if not isinstance(nodes, list):
        return []
    return [node for node in nodes if isinstance(node, dict)]


def search_issues(
    access_token: str,
    *,
    graphql_url: str = LINEAR_GRAPHQL_URL,
    team_id: str | None = None,
    project_id: str | None = None,
    query: str | None = None,
    control_id: str | None = None,
    first: int = 50,
) -> list[dict[str, Any]]:
    filter_input: dict[str, Any] = {}
    if team_id:
        filter_input["team"] = {"id": {"eq": team_id}}
    if project_id:
        filter_input["project"] = {"id": {"eq": project_id}}
    terms = [str(x).strip() for x in (query, control_id) if x and str(x).strip()]
    if terms:
        filter_input["or"] = []
        for term in terms:
            filter_input["or"].append({"title": {"contains": term}})
            filter_input["or"].append({"description": {"contains": term}})

    gql = f"""
    query SearchIssues($first: Int!, $filter: IssueFilter) {{
      issues(first: $first, filter: $filter) {{
        nodes {{
          {_issue_fields()}
        }}
      }}
    }}
    """
    data = _graphql_request(
        access_token,
        gql,
        {"first": first, "filter": filter_input or None},
        graphql_url=graphql_url,
    )
    issues = data.get("issues")
    if not isinstance(issues, dict):
        return []
    nodes = issues.get("nodes")
    if not isinstance(nodes, list):
        return []
    return [node for node in nodes if isinstance(node, dict)]


def create_issue(
    access_token: str,
    *,
    team_id: str,
    title: str,
    description: str | None = None,
    project_id: str | None = None,
    state_id: str | None = None,
    priority: int | None = None,
    assignee_id: str | None = None,
    label_ids: list[str] | None = None,
    graphql_url: str = LINEAR_GRAPHQL_URL,
) -> dict[str, Any]:
    variables: dict[str, Any] = {
        "input": {
            "teamId": team_id,
            "title": title,
        }
    }
    input_data = variables["input"]
    if description is not None:
        input_data["description"] = description
    if project_id:
        input_data["projectId"] = project_id
    if state_id:
        input_data["stateId"] = state_id
    if priority is not None:
        input_data["priority"] = priority
    if assignee_id:
        input_data["assigneeId"] = assignee_id
    if label_ids:
        input_data["labelIds"] = label_ids

    gql = f"""
    mutation CreateIssue($input: IssueCreateInput!) {{
      issueCreate(input: $input) {{
        success
        issue {{
          {_issue_fields()}
        }}
      }}
    }}
    """
    data = _graphql_request(access_token, gql, variables, graphql_url=graphql_url)
    payload = data.get("issueCreate")
    if not isinstance(payload, dict) or not isinstance(payload.get("issue"), dict):
        raise ValueError("Linear did not return an issue from issueCreate.")
    return payload["issue"]


def update_issue(
    access_token: str,
    *,
    issue_id: str,
    title: str | None = None,
    description: str | None = None,
    project_id: str | None = None,
    state_id: str | None = None,
    priority: int | None = None,
    assignee_id: str | None = None,
    label_ids: list[str] | None = None,
    graphql_url: str = LINEAR_GRAPHQL_URL,
) -> dict[str, Any]:
    input_data: dict[str, Any] = {}
    if title is not None:
        input_data["title"] = title
    if description is not None:
        input_data["description"] = description
    if project_id is not None:
        input_data["projectId"] = project_id
    if state_id is not None:
        input_data["stateId"] = state_id
    if priority is not None:
        input_data["priority"] = priority
    if assignee_id is not None:
        input_data["assigneeId"] = assignee_id
    if label_ids is not None:
        input_data["labelIds"] = label_ids

    gql = f"""
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {{
      issueUpdate(id: $id, input: $input) {{
        success
        issue {{
          {_issue_fields()}
        }}
      }}
    }}
    """
    data = _graphql_request(access_token, gql, {"id": issue_id, "input": input_data}, graphql_url=graphql_url)
    payload = data.get("issueUpdate")
    if not isinstance(payload, dict) or not isinstance(payload.get("issue"), dict):
        raise ValueError("Linear did not return an issue from issueUpdate.")
    return payload["issue"]
