"""Map Azure DevOps REST payloads into ``devtools.common_schema``."""

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


def ado_repo_to_unified(raw: dict[str, Any], *, web_base: str, organization: str, project: str) -> DevOpsRepository:
    rid = raw.get("id")
    name = raw.get("name")
    url = raw.get("webUrl") or raw.get("url")
    default_branch = raw.get("defaultBranch")
    if isinstance(default_branch, str) and default_branch.startswith("refs/heads/"):
        default_branch = default_branch.replace("refs/heads/", "", 1)
    full = f"{organization}/{project}/{name}" if name else None
    return DevOpsRepository(
        id=str(rid) if rid is not None else "",
        name=str(name) if name else None,
        full_name=full,
        default_branch=default_branch if isinstance(default_branch, str) else None,
        html_url=str(url) if isinstance(url, str) else None,
        provider="azure_devops",
        raw=raw,
    )


def ado_commit_to_unified(raw: dict[str, Any]) -> DevOpsCommit:
    cid = raw.get("commitId")
    comment = raw.get("comment")
    author = raw.get("author") if isinstance(raw.get("author"), dict) else {}
    return DevOpsCommit(
        id=str(cid) if cid else "",
        message=str(comment) if isinstance(comment, str) else None,
        author_name=author.get("name") if isinstance(author.get("name"), str) else None,
        author_email=author.get("email") if isinstance(author.get("email"), str) else None,
        committed_at=author.get("date") if isinstance(author.get("date"), str) else None,
        html_url=raw.get("remoteUrl") if isinstance(raw.get("remoteUrl"), str) else None,
        provider="azure_devops",
        raw=raw,
    )


def ado_ref_to_unified(raw: dict[str, Any]) -> DevOpsBranch:
    name = raw.get("name")
    ref_name = str(name) if isinstance(name, str) else ""
    short = ref_name.replace("refs/heads/", "", 1) if ref_name.startswith("refs/heads/") else ref_name
    oid = raw.get("objectId")
    return DevOpsBranch(
        name=short,
        sha=str(oid) if isinstance(oid, str) else None,
        protected=None,
        provider="azure_devops",
        raw=raw,
    )


def ado_pr_to_unified(raw: dict[str, Any]) -> DevOpsPullRequest:
    pid = raw.get("pullRequestId")
    st = raw.get("status")
    src = raw.get("sourceRefName") if isinstance(raw.get("sourceRefName"), str) else None
    tgt = raw.get("targetRefName") if isinstance(raw.get("targetRefName"), str) else None
    return DevOpsPullRequest(
        id=str(pid) if pid is not None else "",
        number=int(pid) if isinstance(pid, int) else None,
        title=raw.get("title") if isinstance(raw.get("title"), str) else None,
        state=str(st) if st is not None else None,
        html_url=raw.get("url") if isinstance(raw.get("url"), str) else None,
        head_ref=src.replace("refs/heads/", "", 1) if isinstance(src, str) and src.startswith("refs/heads/") else src,
        base_ref=tgt.replace("refs/heads/", "", 1) if isinstance(tgt, str) and tgt.startswith("refs/heads/") else tgt,
        provider="azure_devops",
        raw=raw,
    )


def ado_build_to_unified(
    raw: dict[str, Any],
    *,
    web_base: str,
    organization: str,
    project: str,
) -> DevOpsPipeline:
    bid = raw.get("id")
    st = raw.get("status")
    res = raw.get("result")
    url = raw.get("url")
    if not url and bid is not None:
        url = f"{web_base}/{organization}/{project}/_build/results?buildId={bid}"
    return DevOpsPipeline(
        id=str(bid) if bid is not None else "",
        name=raw.get("buildNumber") if isinstance(raw.get("buildNumber"), str) else None,
        status=str(st) if st is not None else None,
        conclusion=str(res) if res is not None else None,
        html_url=str(url) if isinstance(url, str) else None,
        created_at=raw.get("queueTime") if isinstance(raw.get("queueTime"), str) else None,
        updated_at=raw.get("finishTime") if isinstance(raw.get("finishTime"), str) else None,
        provider="azure_devops",
        raw=raw,
    )


def ado_timeline_record_to_job(raw: dict[str, Any]) -> DevOpsJob | None:
    if raw.get("type") not in ("Job", "Phase"):
        return None
    rid = raw.get("id")
    return DevOpsJob(
        id=str(rid) if rid is not None else "",
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        status=raw.get("state") if isinstance(raw.get("state"), str) else None,
        conclusion=raw.get("result") if isinstance(raw.get("result"), str) else None,
        started_at=raw.get("startTime") if isinstance(raw.get("startTime"), str) else None,
        completed_at=raw.get("finishTime") if isinstance(raw.get("finishTime"), str) else None,
        provider="azure_devops",
        raw=raw,
    )


def ado_artifact_to_unified(raw: dict[str, Any]) -> DevOpsArtifact:
    aid = raw.get("id")
    res = raw.get("resource") if isinstance(raw.get("resource"), dict) else {}
    download = res.get("downloadUrl") or res.get("url")
    return DevOpsArtifact(
        id=str(aid) if aid is not None else "",
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        size_in_bytes=None,
        created_at=None,
        expires_at=None,
        archive_download_url=str(download) if isinstance(download, str) else None,
        provider="azure_devops",
        raw=raw,
    )


def ado_connection_user_to_unified(raw: dict[str, Any]) -> DevOpsUser:
    """Best-effort from ``connectionData`` ``authenticatedUser``."""
    au = raw.get("authenticatedUser") if isinstance(raw.get("authenticatedUser"), dict) else raw
    if not isinstance(au, dict):
        au = {}
    uid = au.get("id") or au.get("descriptor")
    uname = au.get("providerDisplayName") or au.get("displayName") or au.get("uniqueName")
    mail = au.get("mailAddress") if isinstance(au.get("mailAddress"), str) else None
    return DevOpsUser(
        id=str(uid) if uid is not None else "",
        login=au.get("uniqueName") if isinstance(au.get("uniqueName"), str) else None,
        name=str(uname) if uname else None,
        email=mail,
        html_url=None,
        provider="azure_devops",
        raw=raw if isinstance(raw, dict) else {},
    )


def ado_service_hook_to_event(payload: dict[str, Any], *, event_type: str | None) -> DevOpsEvent:
    return DevOpsEvent(
        id=None,
        event_type=event_type,
        action=payload.get("eventType") if isinstance(payload.get("eventType"), str) else None,
        occurred_at=payload.get("createdDate") if isinstance(payload.get("createdDate"), str) else None,
        provider="azure_devops",
        raw=payload,
    )
