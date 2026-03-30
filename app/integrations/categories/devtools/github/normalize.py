"""Map GitHub REST payloads into ``devtools.common_schema`` models."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.devtools.common_schema import (
    DevOpsArtifact,
    DevOpsBranch,
    DevOpsCommit,
    DevOpsEvent,
    DevOpsJob,
    DevOpsPipeline,
    DevOpsPullRequest,
    DevOpsRepository,
    DevOpsUser,
)


def github_repo_to_unified(raw: dict[str, Any]) -> DevOpsRepository:
    rid = raw.get("id")
    return DevOpsRepository(
        id=str(rid) if rid is not None else "",
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        full_name=raw.get("full_name") if isinstance(raw.get("full_name"), str) else None,
        default_branch=raw.get("default_branch") if isinstance(raw.get("default_branch"), str) else None,
        html_url=raw.get("html_url") if isinstance(raw.get("html_url"), str) else None,
        provider="github",
        raw=raw,
    )


def github_commit_list_item_to_unified(raw: dict[str, Any]) -> DevOpsCommit:
    sha = raw.get("sha")
    commit = raw.get("commit") if isinstance(raw.get("commit"), dict) else {}
    author = commit.get("author") if isinstance(commit.get("author"), dict) else {}
    return DevOpsCommit(
        id=str(sha) if sha else "",
        message=commit.get("message") if isinstance(commit.get("message"), str) else None,
        author_name=author.get("name") if isinstance(author.get("name"), str) else None,
        author_email=author.get("email") if isinstance(author.get("email"), str) else None,
        committed_at=author.get("date") if isinstance(author.get("date"), str) else None,
        html_url=raw.get("html_url") if isinstance(raw.get("html_url"), str) else None,
        provider="github",
        raw=raw,
    )


def github_branch_to_unified(raw: dict[str, Any]) -> DevOpsBranch:
    name = raw.get("name")
    commit = raw.get("commit") if isinstance(raw.get("commit"), dict) else {}
    sha = commit.get("sha")
    prot = raw.get("protected")
    return DevOpsBranch(
        name=str(name) if name is not None else "",
        sha=str(sha) if isinstance(sha, str) else None,
        protected=bool(prot) if isinstance(prot, bool) else None,
        provider="github",
        raw=raw,
    )


def github_pull_to_unified(raw: dict[str, Any]) -> DevOpsPullRequest:
    rid = raw.get("id")
    num = raw.get("number")
    head = raw.get("head") if isinstance(raw.get("head"), dict) else {}
    base = raw.get("base") if isinstance(raw.get("base"), dict) else {}
    return DevOpsPullRequest(
        id=str(rid) if rid is not None else "",
        number=int(num) if isinstance(num, int) else None,
        title=raw.get("title") if isinstance(raw.get("title"), str) else None,
        state=raw.get("state") if isinstance(raw.get("state"), str) else None,
        html_url=raw.get("html_url") if isinstance(raw.get("html_url"), str) else None,
        head_ref=head.get("ref") if isinstance(head.get("ref"), str) else None,
        base_ref=base.get("ref") if isinstance(base.get("ref"), str) else None,
        provider="github",
        raw=raw,
    )


def github_workflow_run_to_unified(raw: dict[str, Any]) -> DevOpsPipeline:
    rid = raw.get("id")
    return DevOpsPipeline(
        id=str(rid) if rid is not None else "",
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        status=raw.get("status") if isinstance(raw.get("status"), str) else None,
        conclusion=raw.get("conclusion") if isinstance(raw.get("conclusion"), str) else None,
        html_url=raw.get("html_url") if isinstance(raw.get("html_url"), str) else None,
        created_at=raw.get("created_at") if isinstance(raw.get("created_at"), str) else None,
        updated_at=raw.get("updated_at") if isinstance(raw.get("updated_at"), str) else None,
        provider="github",
        raw=raw,
    )


def github_job_to_unified(raw: dict[str, Any]) -> DevOpsJob:
    rid = raw.get("id")
    return DevOpsJob(
        id=str(rid) if rid is not None else "",
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        status=raw.get("status") if isinstance(raw.get("status"), str) else None,
        conclusion=raw.get("conclusion") if isinstance(raw.get("conclusion"), str) else None,
        started_at=raw.get("started_at") if isinstance(raw.get("started_at"), str) else None,
        completed_at=raw.get("completed_at") if isinstance(raw.get("completed_at"), str) else None,
        provider="github",
        raw=raw,
    )


def github_artifact_to_unified(raw: dict[str, Any]) -> DevOpsArtifact:
    rid = raw.get("id")
    return DevOpsArtifact(
        id=str(rid) if rid is not None else "",
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        size_in_bytes=raw.get("size_in_bytes") if isinstance(raw.get("size_in_bytes"), int) else None,
        created_at=raw.get("created_at") if isinstance(raw.get("created_at"), str) else None,
        expires_at=raw.get("expires_at") if isinstance(raw.get("expires_at"), str) else None,
        archive_download_url=raw.get("archive_download_url")
        if isinstance(raw.get("archive_download_url"), str)
        else None,
        provider="github",
        raw=raw,
    )


def github_user_to_unified(raw: dict[str, Any]) -> DevOpsUser:
    uid = raw.get("id")
    return DevOpsUser(
        id=str(uid) if uid is not None else "",
        login=raw.get("login") if isinstance(raw.get("login"), str) else None,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        email=raw.get("email") if isinstance(raw.get("email"), str) else None,
        html_url=raw.get("html_url") if isinstance(raw.get("html_url"), str) else None,
        provider="github",
        raw=raw,
    )


def github_webhook_to_event(
    *,
    event_name: str | None,
    delivery_id: str | None,
    payload: dict[str, Any],
) -> DevOpsEvent:
    action = payload.get("action") if isinstance(payload.get("action"), str) else None
    return DevOpsEvent(
        id=delivery_id,
        event_type=event_name,
        action=action,
        occurred_at=None,
        provider="github",
        raw=payload,
    )
