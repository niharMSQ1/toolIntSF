"""Evidence codes for Orca Security (distinct band EV-721+)."""

from __future__ import annotations

from typing import Literal

OrcaStrategy = Literal[
    "alerts_query",
    "alerts_minimal",
    "partial_metadata",
]

ORCA_CSPM_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-721",
        "name": "Orca Security — cloud alerts (query)",
        "category": "CSPM",
        "api_endpoint": "POST .../api/automations/query/alerts",
    },
    {
        "code": "EV-722",
        "name": "Orca Security — API connectivity check",
        "category": "CSPM",
        "api_endpoint": "POST .../api/automations/query/alerts (limit=1)",
    },
    {
        "code": "EV-723",
        "name": "Orca Security — integration metadata",
        "category": "CSPM",
        "api_endpoint": "Token auth (see Cortex XSOAR Orca pack)",
    },
]

ALL_ORCA_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in ORCA_CSPM_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in ORCA_CSPM_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, OrcaStrategy] = {
    "EV-721": "alerts_query",
    "EV-722": "alerts_minimal",
    "EV-723": "partial_metadata",
}
