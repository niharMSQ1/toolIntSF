"""
Shared IAM evidence catalog (EV-* codes) for IDP integrations (Okta, Microsoft Entra).

``evidence_masters.code`` is globally unique in the database; each product seeds the same
codes/names so the catalog aligns across Okta and Entra.
"""

from __future__ import annotations

IAM_EVIDENCE_SEED_ROWS: list[dict[str, str]] = [
    {"code": "EV-37", "name": "User Access Provisioning Records — IAM", "category": "IAM"},
    {"code": "EV-39", "name": "Privileged Access Register — IAM", "category": "IAM"},
    {"code": "EV-40", "name": "Password Manager User Access Reports — IAM", "category": "IAM"},
    {"code": "EV-75", "name": "Access Review Reports — IAM", "category": "IAM"},
    {"code": "EV-77", "name": "Password Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-78", "name": "Authentication System Configuration Reports — IAM", "category": "IAM"},
    {"code": "EV-126", "name": "SSO Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-127", "name": "SSO Authentication Logs — IAM", "category": "IAM"},
    {"code": "EV-151", "name": "Role Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-154", "name": "MFA Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-167", "name": "Backup Access Control Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-189", "name": "Log Access Control Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-207", "name": "Repository Access Control Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-461", "name": "Session Timeout Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-463", "name": "Remote Access Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-476", "name": "Account Lockout Configuration Records — IAM", "category": "IAM"},
    {"code": "EV-522", "name": "Privileged Access Review Reports — IAM", "category": "IAM"},
]

ALL_IAM_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in IAM_EVIDENCE_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in IAM_EVIDENCE_SEED_ROWS)
