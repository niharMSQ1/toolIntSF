from __future__ import annotations

from app.integrations.categories.hrms.zoho_people.api_endpoints import (
    FORM_DEPARTMENT,
    FORM_EMPLOYEE,
    path_forms_get_records,
)

# Canonical paths (matches Zoho docs — see api_endpoints.py).
EMPLOYEE_FORM_GET_RECORDS_PATH = path_forms_get_records(FORM_EMPLOYEE)
DEPARTMENT_FORM_GET_RECORDS_PATH = path_forms_get_records(FORM_DEPARTMENT)

# Zoho People — HR / Employee Management (``hrms`` registry).
#
# `code` and `name` align with **mappings.txt** domain `465c7082-4a36-4567-b535-e6fe16994eec` (HR / Employee Management).
# Each row maps one GRC evidence code (EV-*) to a collector implementation. Collectors call Zoho APIs
# that best match the operational need; titles follow the GRC catalog.
#
# `api` is the relative path (``people_base`` = regional host, e.g. ``https://people.zoho.in``).

_HR_CAT = "HR / Employee Management"

ZOHO_EVIDENCE_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-26",
        "name": "Employee Offboarding Checklist Records — HR",
        "category": _HR_CAT,
        "api": EMPLOYEE_FORM_GET_RECORDS_PATH,
        "collector_key": "exit_employees",
    },
    {
        "code": "EV-521",
        "name": "Role and Responsibility Register — HR",
        "category": _HR_CAT,
        "api": EMPLOYEE_FORM_GET_RECORDS_PATH,
        "collector_key": "employee_master",
    },
    {
        "code": "EV-402",
        "name": "Team Role Assignment Records — HR",
        "category": _HR_CAT,
        "api": EMPLOYEE_FORM_GET_RECORDS_PATH,
        "collector_key": "active_employees",
    },
    {
        "code": "EV-25",
        "name": "Employee Termination Records — HR",
        "category": _HR_CAT,
        "api": EMPLOYEE_FORM_GET_RECORDS_PATH,
        "collector_key": "terminated_employees",
    },
    {
        "code": "EV-128",
        "name": "Organizational Chart — HR",
        "category": _HR_CAT,
        "api": DEPARTMENT_FORM_GET_RECORDS_PATH,
        "collector_key": "department_structure",
    },
    {
        "code": "EV-129",
        "name": "Employee Role and Responsibility Records — HR",
        "category": _HR_CAT,
        "api": EMPLOYEE_FORM_GET_RECORDS_PATH,
        "collector_key": "reporting_hierarchy",
    },
    {
        "code": "EV-564",
        "name": "Employee Reference Check Records — HR",
        "category": _HR_CAT,
        "api": EMPLOYEE_FORM_GET_RECORDS_PATH,
        "collector_key": "employee_email_list",
    },
    {
        "code": "EV-88",
        "name": "Security Awareness Training Records — HR",
        "category": _HR_CAT,
        "api": "/people/api/attendance/getUserReport",
        "collector_key": "attendance_logs",
    },
    {
        "code": "EV-136",
        "name": "Employee Performance Review Records — HR",
        "category": _HR_CAT,
        "api": "/people/api/timetracker/gettimesheet",
        "collector_key": "timesheet_records",
    },
    {
        "code": "EV-137",
        "name": "Employee Probation Review Records — HR",
        "category": _HR_CAT,
        "api": "/api/v2/leavetracker/leaves/records",
        "collector_key": "leave_records",
    },
    {
        "code": "EV-292",
        "name": "Employee Training Records — HR",
        "category": _HR_CAT,
        "api": "/api/v1/courses",
        "collector_key": "training_completion",
    },
    {
        "code": "EV-140",
        "name": "Employee Policy Acknowledgement Records — HR",
        "category": _HR_CAT,
        "api": "/people/api/v3/files/acknowledgement/details",
        "collector_key": "policy_acknowledgement",
    },
    {
        "code": "EV-89",
        "name": "Employee Onboarding Training Records — HR",
        "category": _HR_CAT,
        "api": EMPLOYEE_FORM_GET_RECORDS_PATH,
        "collector_key": "new_hire_records",
    },
    {
        "code": "EV-113",
        "name": "Employee Background Verification Records — HR",
        "category": _HR_CAT,
        "api": "/api/forms/{exitFormLink}/getRecords",
        "collector_key": "exit_clearance",
    },
]

# Collector keys that read the employee form (same path as `EMPLOYEE_FORM_GET_RECORDS_PATH`).
EMPLOYEE_FORM_COLLECTOR_KEYS: frozenset[str] = frozenset(
    row["collector_key"] for row in ZOHO_EVIDENCE_SEED_ROWS if row.get("api") == EMPLOYEE_FORM_GET_RECORDS_PATH
)

EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(row["name"] for row in ZOHO_EVIDENCE_SEED_ROWS)

CODE_TO_COLLECTOR: dict[str, str] = {row["code"]: row["collector_key"] for row in ZOHO_EVIDENCE_SEED_ROWS}

# Deprecated: older HR_* codes (pre–mappings.txt alignment). Kept so existing DB rows still resolve.
_LEGACY_CODE_TO_COLLECTOR: dict[str, str] = {
    "HR_EXIT_EMPLOYEES": "exit_employees",
    "HR_EMPLOYEE_MASTER": "employee_master",
    "HR_ACTIVE_EMPLOYEES": "active_employees",
    "HR_TERMINATED_EMPLOYEES": "terminated_employees",
    "HR_DEPARTMENT_STRUCTURE": "department_structure",
    "HR_REPORTING_STRUCTURE": "reporting_hierarchy",
    "HR_EMPLOYEE_EMAIL_LIST": "employee_email_list",
    "HR_ATTENDANCE_LOGS": "attendance_logs",
    "HR_TIMESHEETS": "timesheet_records",
    "HR_LEAVE_RECORDS": "leave_records",
    "HR_TRAINING_COMPLETION": "training_completion",
    "HR_POLICY_ACKNOWLEDGEMENT": "policy_acknowledgement",
    "HR_NEW_HIRES": "new_hire_records",
    "HR_EXIT_CLEARANCE": "exit_clearance",
}
CODE_TO_COLLECTOR.update(_LEGACY_CODE_TO_COLLECTOR)
