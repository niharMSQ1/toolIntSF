"""Evidence codes for Sysdig Secure (distinct band EV-751+)."""

from __future__ import annotations

from typing import Literal

SysdigStrategy = Literal[
    "agents_connected",
    "user_me_minimal",
    "partial_metadata",
]

SYSDIG_CSPM_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-751",
        "name": "Sysdig Secure — connected agents (inventory)",
        "category": "CSPM",
        "api_endpoint": "GET .../api/agents/connected",
    },
    {
        "code": "EV-752",
        "name": "Sysdig Secure — current user (API connectivity)",
        "category": "CSPM",
        "api_endpoint": "GET .../api/user/me",
    },
    {
        "code": "EV-753",
        "name": "Sysdig Secure — integration metadata",
        "category": "CSPM",
        "api_endpoint": "Bearer token (see Sysdig API docs)",
    },
]

ALL_SYSDIG_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in SYSDIG_CSPM_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in SYSDIG_CSPM_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, SysdigStrategy] = {
    "EV-751": "agents_connected",
    "EV-752": "user_me_minimal",
    "EV-753": "partial_metadata",
}
