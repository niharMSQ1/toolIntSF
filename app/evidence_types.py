"""
Canonical evidence type codes and display names (integration-agnostic).
No DB table: use evidence.code to store these codes.
"""

from typing import NamedTuple
from enum import Enum


class EvidenceType(NamedTuple):
    code: str
    name: str
    domain: str


# HR / People (Zoho, BambooHR, Workday)
HR_EVIDENCE_TYPES = [
    EvidenceType("hr_employee_directory", "Employee Directory", "hr"),
    EvidenceType("hr_department_structure", "Department Structure", "hr"),
    EvidenceType("hr_onboarding_records", "Employee Onboarding Records", "hr"),
    EvidenceType("hr_termination_records", "Employee Termination Records", "hr"),
    EvidenceType("hr_training_completion", "Training Completion Records", "hr"),
]

# IAM / Access (Okta, Azure AD, Google Workspace)
IAM_EVIDENCE_TYPES = [
    EvidenceType("iam_user_list", "User / account list", "iam"),
    EvidenceType("iam_role_assignments", "Role / permission matrix", "iam"),
    EvidenceType("iam_access_revocation_log", "Access revocation log", "iam"),
    EvidenceType("iam_mfa_status", "MFA enforcement status", "iam"),
]

# DevOps / Code (GitHub, GitLab)
DEVOPS_EVIDENCE_TYPES = [
    EvidenceType("devops_branch_protection", "Branch protection state", "devops"),
    EvidenceType("devops_dependency_alerts", "Dependency / Dependabot", "devops"),
    EvidenceType("devops_code_scanning", "SAST / CodeQL status", "devops"),
    EvidenceType("devops_deploy_approvals", "Deployment / change log", "devops"),
]

# Infrastructure / Cloud (AWS, Azure, GCP)
INFRA_EVIDENCE_TYPES = [
    EvidenceType("infra_audit_log_config", "Audit logging config", "infra"),
    EvidenceType("infra_findings", "Security / compliance findings", "infra"),
    EvidenceType("infra_access_keys", "Access key / credential usage", "infra"),
]

# Logging / SIEM
LOG_EVIDENCE_TYPES = [
    EvidenceType("log_audit_events", "Audit / security events", "log"),
]

ALL_EVIDENCE_TYPES = (
    HR_EVIDENCE_TYPES
    + IAM_EVIDENCE_TYPES
    + DEVOPS_EVIDENCE_TYPES
    + INFRA_EVIDENCE_TYPES
    + LOG_EVIDENCE_TYPES
)

CODE_TO_TYPE = {et.code: et for et in ALL_EVIDENCE_TYPES}


def get_evidence_type(code: str) -> EvidenceType | None:
    return CODE_TO_TYPE.get(code)


def get_hr_evidence_codes() -> list[str]:
    return [et.code for et in HR_EVIDENCE_TYPES]
