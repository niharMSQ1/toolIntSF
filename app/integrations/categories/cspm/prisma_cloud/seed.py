"""Re-export Prisma Cloud CSPM seed rows."""

from app.integrations.categories.cspm.prisma_cloud.evidence_map import (
    ALL_PRISMA_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    PRISMA_CSPM_SEED_ROWS,
)

__all__ = [
    "ALL_PRISMA_EVIDENCE_CODES",
    "EVIDENCE_MASTER_NAME_ORDER",
    "PRISMA_CSPM_SEED_ROWS",
]
