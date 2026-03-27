"""Linear issue and workspace data routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.categories.itsm.linear import service
from app.schemas import (
    LinearCreateIssueBody,
    LinearIssueItem,
    LinearIssueMutationResponse,
    LinearIssuesResponse,
    LinearProjectItem,
    LinearProjectsResponse,
    LinearTeamItem,
    LinearTeamsResponse,
    LinearUpdateIssueBody,
    LinearUpsertIssueBody,
)

router = APIRouter(prefix="/api/v1/integrations/linear", tags=["integrations", "itsm", "linear"])


def _issue_to_schema(issue: dict[str, Any]) -> LinearIssueItem:
    team = issue.get("team") if isinstance(issue.get("team"), dict) else {}
    project = issue.get("project") if isinstance(issue.get("project"), dict) else {}
    state = issue.get("state") if isinstance(issue.get("state"), dict) else {}
    return LinearIssueItem(
        id=str(issue.get("id")),
        identifier=str(issue.get("identifier")) if issue.get("identifier") is not None else None,
        title=str(issue.get("title") or ""),
        description=str(issue.get("description")) if issue.get("description") is not None else None,
        url=str(issue.get("url")) if issue.get("url") is not None else None,
        priority=int(issue["priority"]) if issue.get("priority") is not None else None,
        team_id=str(team.get("id")) if team.get("id") is not None else None,
        team_key=str(team.get("key")) if team.get("key") is not None else None,
        team_name=str(team.get("name")) if team.get("name") is not None else None,
        project_id=str(project.get("id")) if project.get("id") is not None else None,
        project_name=str(project.get("name")) if project.get("name") is not None else None,
        state_id=str(state.get("id")) if state.get("id") is not None else None,
        state_name=str(state.get("name")) if state.get("name") is not None else None,
        created_at=str(issue.get("createdAt")) if issue.get("createdAt") is not None else None,
        updated_at=str(issue.get("updatedAt")) if issue.get("updatedAt") is not None else None,
    )


@router.get("/teams", response_model=LinearTeamsResponse)
def list_teams(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> LinearTeamsResponse:
    try:
        rows = service.get_teams(session, org_id=org_id, tool_id=tool_id)
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e
    return LinearTeamsResponse(
        organization_id=org_id,
        tool_id=tool_id,
        teams=[
            LinearTeamItem(
                id=str(row.get("id")),
                key=str(row.get("key")) if row.get("key") is not None else None,
                name=str(row.get("name") or ""),
                description=str(row.get("description")) if row.get("description") is not None else None,
                private=bool(row["private"]) if row.get("private") is not None else None,
                archived_at=str(row.get("archivedAt")) if row.get("archivedAt") is not None else None,
            )
            for row in rows
        ],
    )


@router.get("/projects", response_model=LinearProjectsResponse)
def list_projects(org_id: str, tool_id: str, session: Session = Depends(get_db)) -> LinearProjectsResponse:
    try:
        rows = service.get_projects(session, org_id=org_id, tool_id=tool_id)
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e
    return LinearProjectsResponse(
        organization_id=org_id,
        tool_id=tool_id,
        projects=[
            LinearProjectItem(
                id=str(row.get("id")),
                name=str(row.get("name") or ""),
                description=str(row.get("description")) if row.get("description") is not None else None,
                state=str(row.get("state")) if row.get("state") is not None else None,
                progress=float(row["progress"]) if row.get("progress") is not None else None,
                target_date=str(row.get("targetDate")) if row.get("targetDate") is not None else None,
            )
            for row in rows
        ],
    )


@router.get("/issues", response_model=LinearIssuesResponse)
def list_issues(
    org_id: str,
    tool_id: str,
    session: Session = Depends(get_db),
    team_id: str | None = None,
    project_id: str | None = None,
    query: str | None = None,
    control_id: str | None = None,
) -> LinearIssuesResponse:
    try:
        rows = service.search_issues(
            session,
            org_id=org_id,
            tool_id=tool_id,
            team_id=team_id,
            project_id=project_id,
            query=query,
            control_id=control_id,
        )
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e
    return LinearIssuesResponse(
        organization_id=org_id,
        tool_id=tool_id,
        issues=[_issue_to_schema(row) for row in rows],
    )


@router.post("/issues", response_model=LinearIssueMutationResponse)
def create_issue(body: LinearCreateIssueBody, session: Session = Depends(get_db)) -> LinearIssueMutationResponse:
    try:
        issue = service.create_issue(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            team_id=body.team_id,
            title=body.title,
            description=body.description,
            project_id=body.project_id,
            state_id=body.state_id,
            priority=body.priority,
            assignee_id=body.assignee_id,
            label_ids=body.label_ids,
            control_id=body.control_id,
        )
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e
    return LinearIssueMutationResponse(
        organization_id=body.org_id,
        tool_id=body.tool_id,
        deduplicated=False,
        issue=_issue_to_schema(issue),
    )


@router.patch("/issues/{issue_id}", response_model=LinearIssueMutationResponse)
def update_issue(
    issue_id: str,
    body: LinearUpdateIssueBody,
    session: Session = Depends(get_db),
) -> LinearIssueMutationResponse:
    try:
        issue = service.update_issue(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            issue_id=issue_id,
            title=body.title,
            description=body.description,
            project_id=body.project_id,
            state_id=body.state_id,
            priority=body.priority,
            assignee_id=body.assignee_id,
            label_ids=body.label_ids,
        )
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e
    return LinearIssueMutationResponse(
        organization_id=body.org_id,
        tool_id=body.tool_id,
        deduplicated=False,
        issue=_issue_to_schema(issue),
    )


@router.post("/issues/upsert", response_model=LinearIssueMutationResponse)
def upsert_issue_for_control(
    body: LinearUpsertIssueBody,
    session: Session = Depends(get_db),
) -> LinearIssueMutationResponse:
    try:
        issue, deduplicated = service.create_or_update_issue_for_control(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            control_id=body.control_id,
            team_id=body.team_id,
            title=body.title,
            description=body.description,
            project_id=body.project_id,
            state_id=body.state_id,
            priority=body.priority,
            assignee_id=body.assignee_id,
            label_ids=body.label_ids,
        )
    except ValueError as e:
        msg = str(e)
        code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg) from e
    return LinearIssueMutationResponse(
        organization_id=body.org_id,
        tool_id=body.tool_id,
        deduplicated=deduplicated,
        issue=_issue_to_schema(issue),
    )
