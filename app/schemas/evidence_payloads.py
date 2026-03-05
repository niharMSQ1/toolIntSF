"""
Normalized payload shapes for evidence types (see UNIVERSAL_EVIDENCE_ARCHITECTURE.md).
Used when storing tool_evidence in evidence_collections.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class Meta(BaseModel):
    source: str = "zoho_people"
    total: int | None = None


# ---- hr_employee_directory ----
class EmployeeEntry(BaseModel):
    id: str
    email: str | None = None
    name: str | None = None
    department_id: str | None = None
    department_name: str | None = None
    manager_id: str | None = None
    employment_type: str | None = None  # full_time | contractor | ...
    status: str | None = None  # active | inactive | terminated
    hire_date: date | None = None
    termination_date: date | None = None


class HREmployeeDirectoryPayload(BaseModel):
    collected_at: datetime
    employees: list[EmployeeEntry] = Field(default_factory=list)
    meta: Meta = Field(default_factory=lambda: Meta(source="zoho_people"))


# ---- hr_department_structure ----
class DepartmentEntry(BaseModel):
    id: str
    name: str
    parent_id: str | None = None
    head_count: int = 0


class HRDepartmentStructurePayload(BaseModel):
    collected_at: datetime
    departments: list[DepartmentEntry] = Field(default_factory=list)
    meta: Meta = Field(default_factory=lambda: Meta(source="zoho_people"))


# ---- hr_onboarding_records ----
class OnboardingRecord(BaseModel):
    employee_id: str
    hire_date: date | None = None
    onboarding_complete: bool = False
    background_check_status: str | None = None
    documents_complete: bool = False


class HROnboardingRecordsPayload(BaseModel):
    collected_at: datetime
    records: list[OnboardingRecord] = Field(default_factory=list)
    meta: Meta = Field(default_factory=lambda: Meta(source="zoho_people"))


# ---- hr_termination_records ----
class TerminationRecord(BaseModel):
    employee_id: str
    last_working_date: date | None = None
    offboarding_checklist_complete: bool = False
    access_revoked: bool = False


class HRTerminationRecordsPayload(BaseModel):
    collected_at: datetime
    records: list[TerminationRecord] = Field(default_factory=list)
    meta: Meta = Field(default_factory=lambda: Meta(source="zoho_people"))


# ---- hr_training_completion ----
class TrainingCompletionEntry(BaseModel):
    employee_id: str
    course_id: str
    course_name: str | None = None
    completed_at: datetime | None = None
    acknowledgement: bool = False


class HRTrainingCompletionPayload(BaseModel):
    collected_at: datetime
    completions: list[TrainingCompletionEntry] = Field(default_factory=list)
    meta: Meta = Field(default_factory=lambda: Meta(source="zoho_people"))


# ---- Helpers: payload as dict for JSON storage ----
def payload_to_dict(payload: BaseModel) -> dict[str, Any]:
    return payload.model_dump(mode="json")
