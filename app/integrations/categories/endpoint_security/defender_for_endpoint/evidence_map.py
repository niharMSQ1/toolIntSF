"""Evidence codes for Microsoft Defender for Endpoint (band EV-771+)."""

from __future__ import annotations

from typing import Literal

DefenderEndpointStrategy = Literal[
    "machines_list",
    "alerts_list",
    "vulnerabilities_list",
]

DEFENDER_FOR_ENDPOINT_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-771",
        "name": "Microsoft Defender for Endpoint — machines (inventory)",
        "category": "EDR",
        "api_endpoint": "GET .../api/machines",
    },
    {
        "code": "EV-772",
        "name": "Microsoft Defender for Endpoint — alerts (list)",
        "category": "EDR",
        "api_endpoint": "GET .../api/alerts",
    },
    {
        "code": "EV-773",
        "name": "Microsoft Defender for Endpoint — vulnerabilities by machine/software",
        "category": "VM",
        "api_endpoint": "GET .../api/vulnerabilities/machinesVulnerabilities",
    },
]

ALL_DEFENDER_FOR_ENDPOINT_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in DEFENDER_FOR_ENDPOINT_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in DEFENDER_FOR_ENDPOINT_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, DefenderEndpointStrategy] = {
    "EV-771": "machines_list",
    "EV-772": "alerts_list",
    "EV-773": "vulnerabilities_list",
}
