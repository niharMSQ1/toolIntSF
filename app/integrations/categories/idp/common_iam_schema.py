"""Unified IAM entity shapes for IDP integrations (Ping Identity, Okta, Entra, etc.)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IAMIdentity(BaseModel):
    """Directory user / identity record (vendor-neutral)."""

    id: str
    username: str | None = None
    email: str | None = None
    enabled: bool | None = None
    provider: str = Field(description="Integration key (e.g. ping_identity, okta).")
    raw: dict[str, Any] = Field(default_factory=dict)


class IAMGroup(BaseModel):
    """Group, population, or directory group analog."""

    id: str
    name: str | None = None
    provider: str = "iam"
    raw: dict[str, Any] = Field(default_factory=dict)


class IAMApplication(BaseModel):
    """Registered application / connection (SSO client)."""

    id: str
    name: str | None = None
    enabled: bool | None = None
    provider: str = "iam"
    raw: dict[str, Any] = Field(default_factory=dict)


class IAMAuditEvent(BaseModel):
    """Authentication or admin audit event (subset)."""

    id: str | None = None
    recorded_at: str | None = None
    action_type: str | None = None
    provider: str = "iam"
    raw: dict[str, Any] = Field(default_factory=dict)
