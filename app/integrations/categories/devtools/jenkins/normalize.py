"""Map Jenkins JSON API payloads into ``devtools.common_schema``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.integrations.categories.devtools.common_schema import (
    DevOpsArtifact,
    DevOpsEvent,
    DevOpsJob,
    DevOpsPipeline,
    DevOpsRepository,
    DevOpsUser,
)


def jenkins_job_to_repository(raw: dict[str, Any]) -> DevOpsRepository:
    name = raw.get("name") or raw.get("fullName")
    url = raw.get("url")
    fid = raw.get("fullName") or name
    return DevOpsRepository(
        id=str(fid) if fid else "",
        name=str(name) if name else None,
        full_name=str(fid) if fid else None,
        default_branch=None,
        html_url=str(url) if isinstance(url, str) else None,
        provider="jenkins",
        raw=raw,
    )


def jenkins_build_to_pipeline(raw: dict[str, Any], *, job_url: str | None = None) -> DevOpsPipeline:
    num = raw.get("number")
    res = raw.get("result")
    ts = raw.get("timestamp")
    created = None
    if isinstance(ts, int):
        created = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).isoformat()
    url = raw.get("url") or job_url
    return DevOpsPipeline(
        id=str(num) if num is not None else "",
        name=raw.get("fullDisplayName") if isinstance(raw.get("fullDisplayName"), str) else None,
        status="building" if raw.get("building") else "completed",
        conclusion=str(res) if res is not None else None,
        html_url=str(url) if isinstance(url, str) else None,
        created_at=created,
        updated_at=None,
        provider="jenkins",
        raw=raw,
    )


def _ms_to_iso(ms: object) -> str | None:
    if isinstance(ms, int):
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat()
    return None


def jenkins_wfapi_stage_to_job(raw: dict[str, Any], idx: int) -> DevOpsJob:
    name = raw.get("name")
    st = raw.get("status")
    sm = raw.get("startTimeMillis")
    em = raw.get("endTimeMillis")
    return DevOpsJob(
        id=str(raw.get("id", idx)),
        name=str(name) if name else None,
        status=str(st) if st is not None else None,
        conclusion=raw.get("result") if isinstance(raw.get("result"), str) else None,
        started_at=_ms_to_iso(sm) if isinstance(sm, int) else None,
        completed_at=_ms_to_iso(em) if isinstance(em, int) else None,
        provider="jenkins",
        raw=raw if isinstance(raw, dict) else {},
    )


def jenkins_artifact_to_unified(raw: dict[str, Any], *, build_url: str | None) -> DevOpsArtifact:
    rel = raw.get("relativePath")
    fn = raw.get("fileName") or rel
    url = None
    if build_url and rel:
        url = f"{build_url.rstrip('/')}/artifact/{rel}"
    return DevOpsArtifact(
        id=str(fn) if fn else "",
        name=str(fn) if fn else None,
        size_in_bytes=raw.get("size") if isinstance(raw.get("size"), int) else None,
        created_at=None,
        expires_at=None,
        archive_download_url=url,
        provider="jenkins",
        raw=raw,
    )


def jenkins_user_to_unified(raw: dict[str, Any], *, username: str) -> DevOpsUser:
    return DevOpsUser(
        id=str(raw.get("id", username)),
        login=raw.get("name") or username,
        name=raw.get("fullName") if isinstance(raw.get("fullName"), str) else None,
        email=None,
        html_url=raw.get("absoluteUrl") if isinstance(raw.get("absoluteUrl"), str) else None,
        provider="jenkins",
        raw=raw,
    )


def jenkins_webhook_to_event(payload: dict[str, Any]) -> DevOpsEvent:
    return DevOpsEvent(
        id=None,
        event_type=payload.get("build", {}).get("_class") if isinstance(payload.get("build"), dict) else None,
        action=None,
        occurred_at=None,
        provider="jenkins",
        raw=payload,
    )
