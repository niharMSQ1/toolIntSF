from __future__ import annotations

from app.integrations.categories.idp.iam_evidence_catalog import (
    ALL_IAM_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    IAM_EVIDENCE_SEED_ROWS,
)

JUMPCLOUD_IAM_SEED_ROWS: list[dict[str, str]] = [
    {**row, "api": "JumpCloud GET .../api/v2/systemusers (see JumpCloud API docs)"} for row in IAM_EVIDENCE_SEED_ROWS
]

ALL_JUMPCLOUD_IAM_EVIDENCE_CODES = ALL_IAM_EVIDENCE_CODES
