"""Unified models for HR / employee management integrations (Workday, SuccessFactors, …)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HREmployee(BaseModel):
    id: str
    employee_number: str | None = None
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    hire_date: str | None = None
    termination_date: str | None = None
    employment_status: str | None = None
    manager_id: str | None = None
    department_id: str | None = None
    job_title: str | None = None
    provider: str = "workday"
    raw: dict[str, Any] = Field(default_factory=dict)


class HRDepartment(BaseModel):
    id: str
    name: str | None = None
    code: str | None = None
    parent_id: str | None = None
    provider: str = "workday"
    raw: dict[str, Any] = Field(default_factory=dict)


class HRRole(BaseModel):
    """Job profile / position / role title (vendor-specific)."""

    id: str
    title: str | None = None
    code: str | None = None
    provider: str = "workday"
    raw: dict[str, Any] = Field(default_factory=dict)


class HRManagerRelationship(BaseModel):
    employee_id: str
    manager_employee_id: str | None = None
    provider: str = "workday"
    raw: dict[str, Any] = Field(default_factory=dict)


class HREmploymentStatus(BaseModel):
    employee_id: str
    status: str | None = None
    effective_date: str | None = None
    provider: str = "workday"
    raw: dict[str, Any] = Field(default_factory=dict)


class HRCompensation(BaseModel):
    """Only populated when vendor API exposes allowed compensation fields."""

    employee_id: str
    summary: str | None = None
    currency: str | None = None
    provider: str = "workday"
    raw: dict[str, Any] = Field(default_factory=dict)


class HRTimeOffBalance(BaseModel):
    employee_id: str
    plan_name: str | None = None
    balance: str | None = None
    unit: str | None = None
    provider: str = "workday"
    raw: dict[str, Any] = Field(default_factory=dict)


class HREvent(BaseModel):
    """Hire, update, termination, or generic lifecycle notification."""

    id: str | None = None
    event_type: str | None = None
    employee_id: str | None = None
    occurred_at: str | None = None
    provider: str = "workday"
    raw: dict[str, Any] = Field(default_factory=dict)
