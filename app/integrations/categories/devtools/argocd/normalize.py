"""Map Argo CD Application API objects into ``devtools.common_schema``."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.devtools.common_schema import (
    DevOpsPipeline,
    DevOpsRepository,
    DevOpsUser,
)


def argocd_app_to_repository(raw: dict[str, Any]) -> DevOpsRepository:
    meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    name = meta.get("name")
    spec = raw.get("spec") if isinstance(raw.get("spec"), dict) else {}
    src = spec.get("source") if isinstance(spec.get("source"), dict) else {}
    repo = src.get("repoURL") or src.get("url")
    return DevOpsRepository(
        id=str(name) if name else "",
        name=str(name) if name else None,
        full_name=str(name) if name else None,
        default_branch=src.get("targetRevision") if isinstance(src.get("targetRevision"), str) else None,
        html_url=str(repo) if isinstance(repo, str) else None,
        provider="argocd",
        raw=raw,
    )


def argocd_app_to_pipeline(raw: dict[str, Any]) -> DevOpsPipeline:
    meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    name = meta.get("name")
    st = raw.get("status") if isinstance(raw.get("status"), dict) else {}
    sync = st.get("sync") if isinstance(st.get("sync"), dict) else {}
    hs = st.get("health") if isinstance(st.get("health"), dict) else {}
    op = st.get("operationState") if isinstance(st.get("operationState"), dict) else {}
    return DevOpsPipeline(
        id=str(name) if name else "",
        name=str(name) if name else None,
        status=str(sync.get("status")) if sync.get("status") is not None else None,
        conclusion=str(hs.get("status")) if hs.get("status") is not None else None,
        html_url=None,
        created_at=meta.get("creationTimestamp") if isinstance(meta.get("creationTimestamp"), str) else None,
        updated_at=op.get("finishedAt") if isinstance(op.get("finishedAt"), str) else None,
        provider="argocd",
        raw=raw,
    )


def argocd_account_to_user(raw: dict[str, Any]) -> DevOpsUser:
    return DevOpsUser(
        id=str(raw.get("username", raw.get("name", ""))),
        login=raw.get("username") if isinstance(raw.get("username"), str) else None,
        name=raw.get("name") if isinstance(raw.get("name"), str) else None,
        email=None,
        html_url=None,
        provider="argocd",
        raw=raw,
    )


def argocd_version_to_user(version_blob: dict[str, Any]) -> DevOpsUser:
    """Use version payload when account endpoint is restricted."""
    ver = version_blob.get("Version") or version_blob.get("version")
    return DevOpsUser(
        id="argocd",
        login=None,
        name=str(ver) if ver else "argocd",
        email=None,
        html_url=None,
        provider="argocd",
        raw=version_blob,
    )
