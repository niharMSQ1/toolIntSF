"""
Zoho People integration: OAuth client + normalization into the 5 canonical HR evidence payloads.
"""

from .client import (
    ZohoPeopleClient,
    ZohoPeopleClientError,
    build_authorize_url,
    exchange_auth_code_for_tokens,
)
from .normalizer import (
    normalize_zoho_to_hr_payloads,
    normalize_employee_directory,
    normalize_department_structure,
    normalize_onboarding_records,
    normalize_termination_records,
    normalize_training_completion,
)
from .sync import sync_zoho_evidence

__all__ = [
    "ZohoPeopleClient",
    "ZohoPeopleClientError",
    "build_authorize_url",
    "exchange_auth_code_for_tokens",
    "normalize_zoho_to_hr_payloads",
    "normalize_employee_directory",
    "normalize_department_structure",
    "normalize_onboarding_records",
    "normalize_termination_records",
    "normalize_training_completion",
    "sync_zoho_evidence",
]
