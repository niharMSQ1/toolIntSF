"""Linear ITSM evidence seed rows."""

from app.integrations.categories.itsm.jira.evidence_map import EVIDENCE_MASTER_NAME_ORDER, JIRA_ITSM_SEED_ROWS

LINEAR_ITSM_SEED_ROWS = JIRA_ITSM_SEED_ROWS

ALL_LINEAR_ITSM_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in LINEAR_ITSM_SEED_ROWS)

__all__ = [
    "ALL_LINEAR_ITSM_EVIDENCE_CODES",
    "EVIDENCE_MASTER_NAME_ORDER",
    "LINEAR_ITSM_SEED_ROWS",
]
