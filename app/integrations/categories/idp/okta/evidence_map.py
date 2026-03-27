"""ITSM evidence metadata for Okta: IAM catalog + Okta Admin API path hints."""

from __future__ import annotations

from app.integrations.categories.idp.iam_evidence_catalog import (
    ALL_IAM_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    IAM_EVIDENCE_SEED_ROWS,
)

# Okta Admin API path hints (documentation / api_endpoint on evidence_masters).
_OKTA_API_BY_CODE: dict[str, str] = {
    "EV-37": "/api/v1/users",
    "EV-39": "/api/v1/roles",
    "EV-40": "/api/v1/org/factors",
    "EV-75": "/api/v1/groups",
    "EV-77": "/api/v1/policies",
    "EV-78": "/api/v1/policies",
    "EV-126": "/api/v1/idps",
    "EV-127": "/api/v1/logs",
    "EV-151": "/api/v1/roles",
    "EV-154": "/api/v1/org/factors",
    "EV-167": "/api/v1/policies",
    "EV-189": "/api/v1/org",
    "EV-207": "/api/v1/apps",
    "EV-461": "/api/v1/policies",
    "EV-463": "/api/v1/zones",
    "EV-476": "/api/v1/policies",
    "EV-522": "/api/v1/groups",
}

OKTA_IAM_SEED_ROWS: list[dict[str, str]] = [
    {**row, "api": _OKTA_API_BY_CODE[row["code"]]} for row in IAM_EVIDENCE_SEED_ROWS
]

ALL_OKTA_IAM_EVIDENCE_CODES = ALL_IAM_EVIDENCE_CODES
