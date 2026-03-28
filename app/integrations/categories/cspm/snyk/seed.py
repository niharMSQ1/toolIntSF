"""Snyk evidence seed rows (re-export for seed_service)."""

from app.integrations.categories.cspm.snyk.evidence_map import (
    ALL_SNYK_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    SNYK_SEED_ROWS,
)

__all__ = [
    "ALL_SNYK_EVIDENCE_CODES",
    "EVIDENCE_MASTER_NAME_ORDER",
    "SNYK_SEED_ROWS",
]
