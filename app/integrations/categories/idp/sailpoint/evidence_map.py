from __future__ import annotations

from app.integrations.categories.idp.iam_evidence_catalog import (
    ALL_IAM_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    IAM_EVIDENCE_SEED_ROWS,
)

SAILPOINT_IAM_SEED_ROWS: list[dict[str, str]] = [
    {**row, "api": "IdentityNow V3 GET .../v3/public-identities (see SailPoint docs)"} for row in IAM_EVIDENCE_SEED_ROWS
]

ALL_SAILPOINT_IAM_EVIDENCE_CODES = ALL_IAM_EVIDENCE_CODES
