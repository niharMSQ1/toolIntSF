"""IAM catalog + CyberArk Identity SCIM hint."""

from __future__ import annotations

from app.integrations.categories.idp.iam_evidence_catalog import (
    ALL_IAM_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    IAM_EVIDENCE_SEED_ROWS,
)

CYBER_IAM_SEED_ROWS: list[dict[str, str]] = [
    {**row, "api": "SCIM 2.0 GET .../scim/Users (see CyberArk SCIM docs)"} for row in IAM_EVIDENCE_SEED_ROWS
]

ALL_CYBER_IAM_EVIDENCE_CODES = ALL_IAM_EVIDENCE_CODES
