"""IAM evidence masters for Okta Admin API (EV-* codes)."""

from __future__ import annotations

# Category IAM for all. Primary Admin API path documented per row.
OKTA_IAM_SEED_ROWS: list[dict[str, str]] = [
    {"code": "EV-37", "name": "User Access Provisioning Records — IAM", "category": "IAM", "api": "/api/v1/users"},
    {"code": "EV-39", "name": "Privileged Access Register — IAM", "category": "IAM", "api": "/api/v1/roles"},
    {"code": "EV-40", "name": "Password Manager User Access Reports — IAM", "category": "IAM", "api": "/api/v1/org/factors"},
    {"code": "EV-75", "name": "Access Review Reports — IAM", "category": "IAM", "api": "/api/v1/groups"},
    {"code": "EV-77", "name": "Password Configuration Records — IAM", "category": "IAM", "api": "/api/v1/policies"},
    {"code": "EV-78", "name": "Authentication System Configuration Reports — IAM", "category": "IAM", "api": "/api/v1/policies"},
    {"code": "EV-126", "name": "SSO Configuration Records — IAM", "category": "IAM", "api": "/api/v1/idps"},
    {"code": "EV-127", "name": "SSO Authentication Logs — IAM", "category": "IAM", "api": "/api/v1/logs"},
    {"code": "EV-151", "name": "Role Configuration Records — IAM", "category": "IAM", "api": "/api/v1/roles"},
    {"code": "EV-154", "name": "MFA Configuration Records — IAM", "category": "IAM", "api": "/api/v1/org/factors"},
    {"code": "EV-167", "name": "Backup Access Control Configuration Records — IAM", "category": "IAM", "api": "/api/v1/policies"},
    {"code": "EV-189", "name": "Log Access Control Configuration Records — IAM", "category": "IAM", "api": "/api/v1/org"},
    {"code": "EV-207", "name": "Repository Access Control Configuration Records — IAM", "category": "IAM", "api": "/api/v1/apps"},
    {"code": "EV-461", "name": "Session Timeout Configuration Records — IAM", "category": "IAM", "api": "/api/v1/policies"},
    {"code": "EV-463", "name": "Remote Access Configuration Records — IAM", "category": "IAM", "api": "/api/v1/zones"},
    {"code": "EV-476", "name": "Account Lockout Configuration Records — IAM", "category": "IAM", "api": "/api/v1/policies"},
    {"code": "EV-522", "name": "Privileged Access Review Reports — IAM", "category": "IAM", "api": "/api/v1/groups"},
]

ALL_OKTA_IAM_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in OKTA_IAM_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in OKTA_IAM_SEED_ROWS)
