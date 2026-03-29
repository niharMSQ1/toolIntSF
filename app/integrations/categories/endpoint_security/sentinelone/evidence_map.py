"""Evidence codes for SentinelOne (band EV-781+)."""

from __future__ import annotations

from typing import Literal

SentinelOneStrategy = Literal[
    "agents_list",
    "threats_list",
    "installed_applications_list",
]

SENTINELONE_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-781",
        "name": "SentinelOne — agents (inventory)",
        "category": "EDR",
        "api_endpoint": "GET .../web/api/v2.1/agents",
    },
    {
        "code": "EV-782",
        "name": "SentinelOne — threats (list)",
        "category": "EDR",
        "api_endpoint": "GET .../web/api/v2.1/threats",
    },
    {
        "code": "EV-783",
        "name": "SentinelOne — installed applications (application risk)",
        "category": "VM",
        "api_endpoint": "GET .../web/api/v2.1/installed-applications",
    },
]

ALL_SENTINELONE_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in SENTINELONE_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in SENTINELONE_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, SentinelOneStrategy] = {
    "EV-781": "agents_list",
    "EV-782": "threats_list",
    "EV-783": "installed_applications_list",
}
