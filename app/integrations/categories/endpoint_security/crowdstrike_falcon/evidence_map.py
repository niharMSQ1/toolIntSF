"""Evidence codes for CrowdStrike Falcon (distinct band EV-761+)."""

from __future__ import annotations

from typing import Literal

FalconStrategy = Literal[
    "hosts_query",
    "detects_query",
    "spotlight_vulns",
]

CROWDSTRIKE_FALCON_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-761",
        "name": "CrowdStrike Falcon — host device IDs (query)",
        "category": "EDR",
        "api_endpoint": "GET .../devices/queries/devices/v1",
    },
    {
        "code": "EV-762",
        "name": "CrowdStrike Falcon — detection IDs (query)",
        "category": "EDR",
        "api_endpoint": "GET .../detects/queries/detects/v1",
    },
    {
        "code": "EV-763",
        "name": "CrowdStrike Falcon — Spotlight vulnerabilities (combined)",
        "category": "VM",
        "api_endpoint": "GET .../spotlight/combined/vulnerabilities/v1",
    },
]

ALL_FALCON_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in CROWDSTRIKE_FALCON_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in CROWDSTRIKE_FALCON_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, FalconStrategy] = {
    "EV-761": "hosts_query",
    "EV-762": "detects_query",
    "EV-763": "spotlight_vulns",
}
