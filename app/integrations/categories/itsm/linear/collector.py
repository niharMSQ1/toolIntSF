"""Collect Linear issue details for evidence storage."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.itsm.linear import api_client
from app.integrations.categories.itsm.linear.credentials import project_ids_list, team_ids_list


def _build_scope_pairs(cfg: dict[str, Any]) -> list[tuple[str | None, str | None]]:
    """Collect across configured team/project scopes without evidence-name filtering."""
    team_ids = team_ids_list(cfg)
    project_ids = project_ids_list(cfg)

    if team_ids and project_ids:
        return [(team_id, project_id) for team_id in team_ids for project_id in project_ids]
    if team_ids:
        return [(team_id, None) for team_id in team_ids]
    if project_ids:
        return [(None, project_id) for project_id in project_ids]
    return [(None, None)]


def collect_all_issues(
    cfg: dict[str, Any],
    *,
    access_token: str,
    graphql_url: str,
) -> dict[str, Any]:
    scopes = _build_scope_pairs(cfg)
    seen_issue_ids: set[str] = set()
    issues: list[dict[str, Any]] = []

    for team_id, project_id in scopes:
        data = api_client.search_issues(
            access_token,
            graphql_url=graphql_url,
            query=None,
            team_id=team_id,
            project_id=project_id,
            first=50,
        )
        for issue in data:
            issue_id = str(issue.get("id") or "").strip()
            if issue_id and issue_id in seen_issue_ids:
                continue
            if issue_id:
                seen_issue_ids.add(issue_id)
            issues.append(issue)

    return {
        "integration": "linear",
        "source_api": "https://api.linear.app/graphql",
        "collection_mode": "full_issue_dataset",
        "scopes": [
            {
                "team_id": team_id,
                "project_id": project_id,
            }
            for team_id, project_id in scopes
        ],
        "issues_returned": len(issues),
        "issues": issues,
    }


def collect_for_master(master: dict[str, Any], dataset: dict[str, Any]) -> dict[str, Any]:
    payload = dict(dataset)
    payload["evidence_code"] = master.get("code")
    payload["evidence_name"] = master.get("name")
    return payload


def linear_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
