"""Map TeamCity REST payloads into ``devtools.common_schema``."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.devtools.common_schema import (
    DevOpsArtifact,
    DevOpsPipeline,
    DevOpsRepository,
    DevOpsUser,
)


def teamcity_project_to_repo(raw: dict[str, Any], *, base_url: str) -> DevOpsRepository:
    pid = raw.get("id")
    name = raw.get("name")
    web = raw.get("webUrl")
    if not web and pid:
        web = f"{base_url.rstrip('/')}/project.html?projectId={pid}"
    return DevOpsRepository(
        id=str(pid) if pid is not None else "",
        name=str(name) if name else None,
        full_name=str(name) if name else None,
        default_branch=None,
        html_url=str(web) if isinstance(web, str) else None,
        provider="teamcity",
        raw=raw,
    )


def teamcity_build_to_pipeline(raw: dict[str, Any], *, base_url: str) -> DevOpsPipeline:
    bid = raw.get("id")
    num = raw.get("number")
    st = raw.get("state") or raw.get("status")
    web = raw.get("webUrl")
    if not web and bid is not None:
        web = f"{base_url.rstrip('/')}/viewLog.html?buildId={bid}"
    return DevOpsPipeline(
        id=str(bid) if bid is not None else "",
        name=str(raw.get("buildTypeId", "")) if raw.get("buildTypeId") else None,
        status=str(st) if st is not None else None,
        conclusion=raw.get("statusText") if isinstance(raw.get("statusText"), str) else None,
        html_url=str(web) if isinstance(web, str) else None,
        created_at=raw.get("startDate") if isinstance(raw.get("startDate"), str) else None,
        updated_at=raw.get("finishDate") if isinstance(raw.get("finishDate"), str) else None,
        provider="teamcity",
        raw=raw,
    )


def teamcity_server_to_user(server_blob: dict[str, Any]) -> DevOpsUser:
    ver = server_blob.get("version") or server_blob.get("versionMajor")
    return DevOpsUser(
        id="teamcity",
        login=None,
        name=str(ver) if ver else "TeamCity",
        email=None,
        html_url=None,
        provider="teamcity",
        raw=server_blob,
    )


def teamcity_artifact_to_unified(raw: dict[str, Any]) -> DevOpsArtifact:
    name = raw.get("name")
    size = raw.get("size")
    return DevOpsArtifact(
        id=str(name) if name else "",
        name=str(name) if name else None,
        size_in_bytes=int(size) if isinstance(size, (int, str)) and str(size).isdigit() else None,
        created_at=None,
        expires_at=None,
        archive_download_url=raw.get("content", {}).get("href")
        if isinstance(raw.get("content"), dict)
        else raw.get("href"),
        provider="teamcity",
        raw=raw,
    )
