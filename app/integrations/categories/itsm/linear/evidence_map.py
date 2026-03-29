"""ITSM evidence masters for Linear (EV-* codes) and collection metadata."""

from __future__ import annotations

from app.integrations.categories.itsm.jira.evidence_map import JIRA_ITSM_SEED_ROWS


LINEAR_ITSM_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": row["code"],
        "name": row["name"],
        "category": row["category"],
        "api": "/graphql",
    }
    for row in JIRA_ITSM_SEED_ROWS
]

ALL_LINEAR_ITSM_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in LINEAR_ITSM_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in LINEAR_ITSM_SEED_ROWS)

