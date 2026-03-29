"""BambooHR evidence catalog for HRMS evidence collection."""

from __future__ import annotations

_HR_CAT = "HR / Employee Management"
_DIR_API = "/employees/directory"


BAMBOOHR_EVIDENCE_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-521",
        "name": "Role and Responsibility Register — HR",
        "category": _HR_CAT,
        "api": _DIR_API,
        "collector_key": "employee_master",
    },
    {
        "code": "EV-402",
        "name": "Team Role Assignment Records — HR",
        "category": _HR_CAT,
        "api": _DIR_API,
        "collector_key": "active_employees",
    },
    {
        "code": "EV-25",
        "name": "Employee Termination Records — HR",
        "category": _HR_CAT,
        "api": _DIR_API,
        "collector_key": "terminated_employees",
    },
    {
        "code": "EV-128",
        "name": "Organizational Chart — HR",
        "category": _HR_CAT,
        "api": _DIR_API,
        "collector_key": "org_chart",
    },
    {
        "code": "EV-129",
        "name": "Employee Role and Responsibility Records — HR",
        "category": _HR_CAT,
        "api": _DIR_API,
        "collector_key": "reporting_hierarchy",
    },
    {
        "code": "EV-89",
        "name": "Employee Onboarding Training Records — HR",
        "category": _HR_CAT,
        "api": _DIR_API,
        "collector_key": "new_hires",
    },
]

EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(row["name"] for row in BAMBOOHR_EVIDENCE_SEED_ROWS)
CODE_TO_COLLECTOR: dict[str, str] = {row["code"]: row["collector_key"] for row in BAMBOOHR_EVIDENCE_SEED_ROWS}

