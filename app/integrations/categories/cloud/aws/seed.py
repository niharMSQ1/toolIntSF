"""AWS Cloud evidence seed rows (re-export for seed_service)."""

from app.integrations.categories.cloud.aws.evidence_map import (
    ALL_AWS_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    AWS_SEED_ROWS,
)

__all__ = [
    "ALL_AWS_EVIDENCE_CODES",
    "EVIDENCE_MASTER_NAME_ORDER",
    "AWS_SEED_ROWS",
]
