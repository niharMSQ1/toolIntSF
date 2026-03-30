from __future__ import annotations

from app.integrations.categories.idp.iam_evidence_catalog import (
    ALL_IAM_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    IAM_EVIDENCE_SEED_ROWS,
)

FORGEROCK_IAM_SEED_ROWS: list[dict[str, str]] = [
    {**row, "api": "ForgeRock OpenIDM/REST GET managed users (deployment-specific path)"}
    for row in IAM_EVIDENCE_SEED_ROWS
]

ALL_FORGEROCK_IAM_EVIDENCE_CODES = ALL_IAM_EVIDENCE_CODES
