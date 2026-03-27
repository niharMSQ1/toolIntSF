"""Linear ITSM service helpers for issue operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.itsm.linear import api_client
from app.integrations.categories.itsm.linear.credentials import resolve_access_token, resolve_graphql_url
from app.integrations.categories.itsm.linear.token_refresh import refresh_linear_access_tokens
from app.integrations.core.persistence import tool_integration_service as persistence

CONTROL_MARKER = "GRC Control ID:"


def _load_ready_integration(session: Session, org_id: str, tool_id: str) -> dict[str, Any]:
    row = persistence.get_integration(session, org_id, tool_id)
    if not row:
        raise ValueError("Integration not found; configure the tool first.")
    cfg, _ = refresh_linear_access_tokens(session, row, force=False)
    token = resolve_access_token(cfg)
    if not token:
        raise ValueError("Complete Linear OAuth first (access token missing).")
    return {
        "row": row,
        "cfg": cfg,
        "access_token": token,
        "graphql_url": resolve_graphql_url(cfg),
    }


def _issue_marker(control_id: str) -> str:
    return f"{CONTROL_MARKER} {control_id}"


def append_control_marker(description: str | None, control_id: str | None) -> str | None:
    if not control_id:
        return description
    marker = _issue_marker(control_id)
    current = (description or "").strip()
    if marker in current:
        return current
    if current:
        return f"{current}\n\n{marker}"
    return marker


def issue_matches_control(issue: dict[str, Any], control_id: str) -> bool:
    description = str(issue.get("description") or "")
    title = str(issue.get("title") or "")
    marker = _issue_marker(control_id)
    return marker in description or control_id in title


def get_teams(session: Session, *, org_id: str, tool_id: str) -> list[dict[str, Any]]:
    ready = _load_ready_integration(session, org_id, tool_id)
    return api_client.get_teams(
        ready["access_token"],
        graphql_url=ready["graphql_url"],
    )


def get_projects(session: Session, *, org_id: str, tool_id: str) -> list[dict[str, Any]]:
    ready = _load_ready_integration(session, org_id, tool_id)
    return api_client.get_projects(
        ready["access_token"],
        graphql_url=ready["graphql_url"],
    )


def search_issues(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    team_id: str | None = None,
    project_id: str | None = None,
    query: str | None = None,
    control_id: str | None = None,
) -> list[dict[str, Any]]:
    ready = _load_ready_integration(session, org_id, tool_id)
    return api_client.search_issues(
        ready["access_token"],
        graphql_url=ready["graphql_url"],
        team_id=team_id,
        project_id=project_id,
        query=query,
        control_id=control_id,
    )


def create_issue(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    team_id: str,
    title: str,
    description: str | None = None,
    project_id: str | None = None,
    state_id: str | None = None,
    priority: int | None = None,
    assignee_id: str | None = None,
    label_ids: list[str] | None = None,
    control_id: str | None = None,
) -> dict[str, Any]:
    ready = _load_ready_integration(session, org_id, tool_id)
    return api_client.create_issue(
        ready["access_token"],
        graphql_url=ready["graphql_url"],
        team_id=team_id,
        title=title,
        description=append_control_marker(description, control_id),
        project_id=project_id,
        state_id=state_id,
        priority=priority,
        assignee_id=assignee_id,
        label_ids=label_ids,
    )


def update_issue(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    issue_id: str,
    title: str | None = None,
    description: str | None = None,
    project_id: str | None = None,
    state_id: str | None = None,
    priority: int | None = None,
    assignee_id: str | None = None,
    label_ids: list[str] | None = None,
) -> dict[str, Any]:
    ready = _load_ready_integration(session, org_id, tool_id)
    return api_client.update_issue(
        ready["access_token"],
        graphql_url=ready["graphql_url"],
        issue_id=issue_id,
        title=title,
        description=description,
        project_id=project_id,
        state_id=state_id,
        priority=priority,
        assignee_id=assignee_id,
        label_ids=label_ids,
    )


def create_or_update_issue_for_control(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    control_id: str,
    team_id: str,
    title: str,
    description: str | None = None,
    project_id: str | None = None,
    state_id: str | None = None,
    priority: int | None = None,
    assignee_id: str | None = None,
    label_ids: list[str] | None = None,
) -> tuple[dict[str, Any], bool]:
    matches = search_issues(
        session,
        org_id=org_id,
        tool_id=tool_id,
        team_id=team_id,
        project_id=project_id,
        control_id=control_id,
    )
    for issue in matches:
        if issue_matches_control(issue, control_id):
            updated = update_issue(
                session,
                org_id=org_id,
                tool_id=tool_id,
                issue_id=str(issue["id"]),
                title=title,
                description=append_control_marker(description, control_id),
                project_id=project_id,
                state_id=state_id,
                priority=priority,
                assignee_id=assignee_id,
                label_ids=label_ids,
            )
            return updated, True

    created = create_issue(
        session,
        org_id=org_id,
        tool_id=tool_id,
        team_id=team_id,
        title=title,
        description=description,
        project_id=project_id,
        state_id=state_id,
        priority=priority,
        assignee_id=assignee_id,
        label_ids=label_ids,
        control_id=control_id,
    )
    return created, False
