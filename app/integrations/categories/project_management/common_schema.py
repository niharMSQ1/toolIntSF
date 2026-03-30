"""Unified internal models for project-management providers (Asana, Monday, etc.)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UnifiedProject(BaseModel):
    """Normalized project / portfolio container."""

    id: str = Field(description="Provider-stable resource id (e.g. Asana gid).")
    name: str | None = None
    provider: str = Field(description="Integration key, e.g. asana.")
    archived: bool | None = None
    permalink_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict, description="Subset of vendor JSON for debugging.")


class UnifiedUser(BaseModel):
    id: str
    name: str | None = None
    email: str | None = None
    provider: str = "asana"
    raw: dict[str, Any] = Field(default_factory=dict)


class UnifiedStatus(BaseModel):
    """Workflow column / section / status label when the vendor exposes it."""

    label: str | None = None
    resource_type: str | None = Field(default=None, description="e.g. section, task_status.")
    provider: str = "asana"


class UnifiedTask(BaseModel):
    id: str
    name: str | None = None
    completed: bool | None = None
    due_on: str | None = None
    due_at: str | None = None
    assignee_user_id: str | None = None
    project_ids: list[str] = Field(default_factory=list)
    status: UnifiedStatus | None = None
    permalink_url: str | None = None
    provider: str = "asana"
    raw: dict[str, Any] = Field(default_factory=dict)


class UnifiedActivity(BaseModel):
    """Comment, system story, or other activity line (vendor-specific)."""

    id: str
    resource_type: str | None = Field(default=None, description="e.g. story, comment.")
    text: str | None = None
    created_at: str | None = None
    created_by_user_id: str | None = None
    provider: str = "asana"
    raw: dict[str, Any] = Field(default_factory=dict)
