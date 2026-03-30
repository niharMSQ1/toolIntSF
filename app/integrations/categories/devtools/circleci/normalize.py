"""Map CircleCI API v2 into ``devtools.common_schema``."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.devtools.common_schema import (
    DevOpsJob,
    DevOpsPipeline,
    DevOpsRepository,
    DevOpsUser,
)


def circleci_project_to_repo(raw: dict[str, Any]) -> DevOpsRepository:
    slug = raw.get("slug") or raw.get("name")
    rid = raw.get("id")
    vcs = raw.get("vcs_url") or raw.get("vcs", {}).get("url") if isinstance(raw.get("vcs"), dict) else raw.get("vcs_url")
    return DevOpsRepository(
        id=str(rid) if rid is not None else str(slug or ""),
        name=str(slug) if slug else None,
        full_name=str(slug) if slug else None,
        default_branch=raw.get("default_branch") if isinstance(raw.get("default_branch"), str) else None,
        html_url=str(vcs) if isinstance(vcs, str) else None,
        provider="circleci",
        raw=raw,
    )


def circleci_workflow_to_unified(raw: dict[str, Any]) -> DevOpsPipeline:
    wid = raw.get("id")
    st = raw.get("status")
    return DevOpsPipeline(
        id=str(wid) if wid is not None else "",
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        status=str(st) if st is not None else None,
        conclusion=None,
        html_url=None,
        created_at=raw.get("created_at") if isinstance(raw.get("created_at"), str) else None,
        updated_at=raw.get("stopped_at") if isinstance(raw.get("stopped_at"), str) else None,
        provider="circleci",
        raw=raw,
    )


def circleci_pipeline_to_unified(raw: dict[str, Any]) -> DevOpsPipeline:
    pid = raw.get("id")
    st = raw.get("state")
    return DevOpsPipeline(
        id=str(pid) if pid is not None else "",
        name=None,
        status=str(st) if st is not None else None,
        conclusion=None,
        html_url=None,
        created_at=raw.get("created_at") if isinstance(raw.get("created_at"), str) else None,
        updated_at=raw.get("updated_at") if isinstance(raw.get("updated_at"), str) else None,
        provider="circleci",
        raw=raw,
    )


def circleci_workflow_job_to_unified(raw: dict[str, Any]) -> DevOpsJob:
    jid = raw.get("id")
    return DevOpsJob(
        id=str(jid) if jid is not None else "",
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        status=raw.get("status") if isinstance(raw.get("status"), str) else None,
        conclusion=raw.get("outcome") if isinstance(raw.get("outcome"), str) else None,
        started_at=raw.get("started_at") if isinstance(raw.get("started_at"), str) else None,
        completed_at=raw.get("stopped_at") if isinstance(raw.get("stopped_at"), str) else None,
        provider="circleci",
        raw=raw,
    )


def circleci_me_to_user(raw: dict[str, Any]) -> DevOpsUser:
    return DevOpsUser(
        id=str(raw.get("id", raw.get("login", ""))),
        login=raw.get("login") if isinstance(raw.get("login"), str) else None,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        email=None,
        html_url=None,
        provider="circleci",
        raw=raw,
    )
