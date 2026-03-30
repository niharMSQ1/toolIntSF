"""Unified models for DevOps / source-control integrations (GitHub, GitLab, …)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DevOpsRepository(BaseModel):
    id: str
    name: str | None = None
    full_name: str | None = None
    default_branch: str | None = None
    html_url: str | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)


class DevOpsCommit(BaseModel):
    id: str = Field(description="Commit SHA.")
    message: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    committed_at: str | None = None
    html_url: str | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)


class DevOpsBranch(BaseModel):
    name: str
    sha: str | None = None
    protected: bool | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)


class DevOpsPullRequest(BaseModel):
    id: str
    number: int | None = None
    title: str | None = None
    state: str | None = None
    html_url: str | None = None
    head_ref: str | None = None
    base_ref: str | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)


class DevOpsPipeline(BaseModel):
    """CI workflow run / pipeline execution."""

    id: str
    name: str | None = None
    status: str | None = None
    conclusion: str | None = None
    html_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)


class DevOpsJob(BaseModel):
    id: str
    name: str | None = None
    status: str | None = None
    conclusion: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)


class DevOpsArtifact(BaseModel):
    id: str
    name: str | None = None
    size_in_bytes: int | None = None
    created_at: str | None = None
    expires_at: str | None = None
    archive_download_url: str | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)


class DevOpsUser(BaseModel):
    id: str
    login: str | None = None
    name: str | None = None
    email: str | None = None
    html_url: str | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)


class DevOpsEvent(BaseModel):
    """Webhook or audit event (normalized subset)."""

    id: str | None = None
    event_type: str | None = None
    action: str | None = None
    occurred_at: str | None = None
    provider: str = "github"
    raw: dict[str, Any] = Field(default_factory=dict)
