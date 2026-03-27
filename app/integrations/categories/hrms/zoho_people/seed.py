from __future__ import annotations

# Zoho People — HR / Employee Management (registry category remains ``hrms``; GRC domain in
# ``mappings.txt`` aligns with **HR / Employee Management**, e.g. domain_id
# ``465c7082-4a36-4567-b535-e6fe16994eec`` and EV-* codes for HR evidence).
#
# 14 evidence masters — order matches please_readmes/0002 (table rows 1–14).
# ``name`` must match evidence_masters / evidence.title per 0001 & 0002 (G3/G4).
# ``api`` is documentation (relative paths; base = Zoho People regional URL — see api_endpoints.py).
# Collectors use ``code`` + CODE_TO_COLLECTOR.

_HR_CAT = "HR / Employee Management"

ZOHO_EVIDENCE_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "HR_EXIT_EMPLOYEES",
        "name": "Exit Employee Records",
        "category": _HR_CAT,
        "api": "/api/forms/employee/getRecords",
        "collector_key": "exit_employees",
    },
    {
        "code": "HR_EMPLOYEE_MASTER",
        "name": "Employee Master List",
        "category": _HR_CAT,
        "api": "/api/forms/employee/getRecords",
        "collector_key": "employee_master",
    },
    {
        "code": "HR_ACTIVE_EMPLOYEES",
        "name": "Active Employees List",
        "category": _HR_CAT,
        "api": "/api/forms/employee/getRecords",
        "collector_key": "active_employees",
    },
    {
        "code": "HR_TERMINATED_EMPLOYEES",
        "name": "Terminated Employees List",
        "category": _HR_CAT,
        "api": "/api/forms/employee/getRecords",
        "collector_key": "terminated_employees",
    },
    {
        "code": "HR_DEPARTMENT_STRUCTURE",
        "name": "Department Structure",
        "category": _HR_CAT,
        "api": "/api/forms/department/getRecords",
        "collector_key": "department_structure",
    },
    {
        "code": "HR_REPORTING_STRUCTURE",
        "name": "Reporting Hierarchy",
        "category": _HR_CAT,
        "api": "/api/forms/employee/getRecords",
        "collector_key": "reporting_hierarchy",
    },
    {
        "code": "HR_EMPLOYEE_EMAIL_LIST",
        "name": "Employee Email List",
        "category": _HR_CAT,
        "api": "/api/forms/employee/getRecords",
        "collector_key": "employee_email_list",
    },
    {
        "code": "HR_ATTENDANCE_LOGS",
        "name": "Attendance Logs",
        "category": _HR_CAT,
        "api": "/people/api/attendance/getUserReport",
        "collector_key": "attendance_logs",
    },
    {
        "code": "HR_TIMESHEETS",
        "name": "Timesheet Records",
        "category": _HR_CAT,
        "api": "/people/api/timetracker/gettimesheet",
        "collector_key": "timesheet_records",
    },
    {
        "code": "HR_LEAVE_RECORDS",
        "name": "Leave Records",
        "category": _HR_CAT,
        "api": "/api/v2/leavetracker/leaves/records",
        "collector_key": "leave_records",
    },
    {
        "code": "HR_TRAINING_COMPLETION",
        "name": "Training Completion Records",
        "category": _HR_CAT,
        "api": "/api/v1/courses",
        "collector_key": "training_completion",
    },
    {
        "code": "HR_POLICY_ACKNOWLEDGEMENT",
        "name": "Policy Acknowledgement Records",
        "category": _HR_CAT,
        "api": "/people/api/v3/files/acknowledgement/details",
        "collector_key": "policy_acknowledgement",
    },
    {
        "code": "HR_NEW_HIRES",
        "name": "New Hire Records",
        "category": _HR_CAT,
        "api": "/api/forms/employee/getRecords",
        "collector_key": "new_hire_records",
    },
    {
        "code": "HR_EXIT_CLEARANCE",
        "name": "Exit Clearance Status",
        "category": _HR_CAT,
        "api": "/api/forms/{exitFormLink}/getRecords",
        "collector_key": "exit_clearance",
    },
]

EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(row["name"] for row in ZOHO_EVIDENCE_SEED_ROWS)

CODE_TO_COLLECTOR: dict[str, str] = {row["code"]: row["collector_key"] for row in ZOHO_EVIDENCE_SEED_ROWS}
