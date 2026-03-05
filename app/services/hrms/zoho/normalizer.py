"""
Normalize raw Zoho People–style API data into the 5 canonical HR evidence payloads.
Input is arbitrary dicts (e.g. from Zoho employees, departments, forms); output is
payloads ready for evidence_collections.tool_evidence.
"""

from datetime import date, datetime
from typing import Any

from app.schemas.evidence_payloads import (
    HREmployeeDirectoryPayload,
    HRDepartmentStructurePayload,
    HROnboardingRecordsPayload,
    HRTerminationRecordsPayload,
    HRTrainingCompletionPayload,
    EmployeeEntry,
    DepartmentEntry,
    OnboardingRecord,
    TerminationRecord,
    TrainingCompletionEntry,
)


def _parse_date(v: Any) -> date | None:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
        except Exception:
            pass
    return None


def _parse_datetime(v: Any) -> datetime | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            pass
    return None


def normalize_employee_directory(raw_employees: list[dict[str, Any]], collected_at: datetime | None = None) -> dict[str, Any]:
    """Build hr_employee_directory payload from list of employee-like dicts (Zoho API shape)."""
    collected_at = collected_at or datetime.utcnow()
    employees = []
    for e in raw_employees or []:
        emp_id = str(e.get("id") or e.get("employee_id") or e.get("EmployeeID") or "")
        if not emp_id:
            continue
        employees.append(
            EmployeeEntry(
                id=emp_id,
                email=e.get("email") or e.get("Email") or e.get("work_email"),
                name=e.get("name") or e.get("full_name") or e.get("firstName", "") + " " + e.get("lastName", ""),
                department_id=str(e.get("department_id") or e.get("DepartmentID") or "") or None,
                department_name=e.get("department_name") or e.get("DepartmentName"),
                manager_id=str(e.get("manager_id") or e.get("ManagerID") or "") or None,
                employment_type=e.get("employment_type") or e.get("EmploymentType") or e.get("empType"),
                status=e.get("status") or e.get("Status") or "active",
                hire_date=_parse_date(e.get("hire_date") or e.get("joiningDate") or e.get("dateOfJoin")),
                termination_date=_parse_date(e.get("termination_date") or e.get("relievingDate") or e.get("lastWorkingDate")),
            )
        )
    payload = HREmployeeDirectoryPayload(collected_at=collected_at, employees=employees)
    payload.meta.total = len(employees)
    return payload.model_dump(mode="json")


def normalize_department_structure(raw_departments: list[dict[str, Any]], collected_at: datetime | None = None) -> dict[str, Any]:
    """Build hr_department_structure payload from list of department-like dicts (Zoho API shape)."""
    collected_at = collected_at or datetime.utcnow()
    departments = []
    for d in raw_departments or []:
        dept_id = str(d.get("id") or d.get("department_id") or d.get("DepartmentID") or "")
        if not dept_id:
            continue
        departments.append(
            DepartmentEntry(
                id=dept_id,
                name=str(d.get("name") or d.get("department_name") or d.get("DepartmentName") or ""),
                parent_id=str(d.get("parent_id") or d.get("parentId") or d.get("ParentDepartmentID") or "") or None,
                head_count=int(d.get("head_count") or d.get("headCount") or d.get("employee_count") or 0),
            )
        )
    payload = HRDepartmentStructurePayload(collected_at=collected_at, departments=departments)
    return payload.model_dump(mode="json")


def normalize_onboarding_records(raw_records: list[dict[str, Any]], collected_at: datetime | None = None) -> dict[str, Any]:
    """Build hr_onboarding_records payload from Zoho-style onboarding data."""
    collected_at = collected_at or datetime.utcnow()
    records = []
    for r in raw_records or []:
        emp_id = str(r.get("employee_id") or r.get("EmployeeID") or r.get("id") or "")
        if not emp_id:
            continue
        records.append(
            OnboardingRecord(
                employee_id=emp_id,
                hire_date=_parse_date(r.get("hire_date") or r.get("joiningDate") or r.get("dateOfJoin")),
                onboarding_complete=bool(r.get("onboarding_complete") or r.get("onboardingComplete") or r.get("checklist_complete")),
                background_check_status=r.get("background_check_status") or r.get("backgroundCheckStatus"),
                documents_complete=bool(r.get("documents_complete") or r.get("documentsComplete")),
            )
        )
    payload = HROnboardingRecordsPayload(collected_at=collected_at, records=records)
    return payload.model_dump(mode="json")


def normalize_termination_records(raw_records: list[dict[str, Any]], collected_at: datetime | None = None) -> dict[str, Any]:
    """Build hr_termination_records payload from Zoho-style termination data."""
    collected_at = collected_at or datetime.utcnow()
    records = []
    for r in raw_records or []:
        emp_id = str(r.get("employee_id") or r.get("EmployeeID") or r.get("id") or "")
        if not emp_id:
            continue
        records.append(
            TerminationRecord(
                employee_id=emp_id,
                last_working_date=_parse_date(r.get("last_working_date") or r.get("lastWorkingDate") or r.get("relievingDate")),
                offboarding_checklist_complete=bool(r.get("offboarding_checklist_complete") or r.get("offboardingChecklistComplete")),
                access_revoked=bool(r.get("access_revoked") or r.get("accessRevoked")),
            )
        )
    payload = HRTerminationRecordsPayload(collected_at=collected_at, records=records)
    return payload.model_dump(mode="json")


def normalize_training_completion(raw_completions: list[dict[str, Any]], collected_at: datetime | None = None) -> dict[str, Any]:
    """Build hr_training_completion payload from Zoho-style training/completion data."""
    collected_at = collected_at or datetime.utcnow()
    completions = []
    for c in raw_completions or []:
        emp_id = str(c.get("employee_id") or c.get("EmployeeID") or c.get("userId") or "")
        course_id = str(c.get("course_id") or c.get("courseId") or c.get("training_id") or c.get("id") or "")
        if not emp_id and not course_id:
            continue
        completions.append(
            TrainingCompletionEntry(
                employee_id=emp_id or "",
                course_id=course_id or "",
                course_name=c.get("course_name") or c.get("courseName") or c.get("trainingName"),
                completed_at=_parse_datetime(c.get("completed_at") or c.get("completedAt") or c.get("completionDate")),
                acknowledgement=bool(c.get("acknowledgement") or c.get("acknowledgment") or c.get("acknowledged")),
            )
        )
    payload = HRTrainingCompletionPayload(collected_at=collected_at, completions=completions)
    return payload.model_dump(mode="json")


def normalize_zoho_to_hr_payloads(
    *,
    employees: list[dict[str, Any]] | None = None,
    departments: list[dict[str, Any]] | None = None,
    onboarding_records: list[dict[str, Any]] | None = None,
    termination_records: list[dict[str, Any]] | None = None,
    training_completions: list[dict[str, Any]] | None = None,
    collected_at: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Return a dict of evidence_type_code -> normalized payload (for tool_evidence).
    Only includes keys for which input was provided (non-empty or explicitly passed).
    """
    collected_at = collected_at or datetime.utcnow()
    out: dict[str, dict[str, Any]] = {}
    if employees is not None:
        out["hr_employee_directory"] = normalize_employee_directory(employees, collected_at)
    if departments is not None:
        out["hr_department_structure"] = normalize_department_structure(departments, collected_at)
    if onboarding_records is not None:
        out["hr_onboarding_records"] = normalize_onboarding_records(onboarding_records, collected_at)
    if termination_records is not None:
        out["hr_termination_records"] = normalize_termination_records(termination_records, collected_at)
    if training_completions is not None:
        out["hr_training_completion"] = normalize_training_completion(training_completions, collected_at)
    return out
