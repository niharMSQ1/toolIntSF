"""Evidence codes for Aqua Security CSP (distinct band EV-741+)."""

from __future__ import annotations

from typing import Literal

AquaStrategy = Literal[
    "hosts_list",
    "images_minimal",
    "partial_metadata",
]

AQUA_CSPM_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-741",
        "name": "Aqua Security — registered hosts (list)",
        "category": "CSPM",
        "api_endpoint": "GET .../api/v1/hosts",
    },
    {
        "code": "EV-742",
        "name": "Aqua Security — container images (list)",
        "category": "CSPM",
        "api_endpoint": "GET .../api/v1/images",
    },
    {
        "code": "EV-743",
        "name": "Aqua Security — integration metadata",
        "category": "CSPM",
        "api_endpoint": "POST .../api/v1/login",
    },
]

ALL_AQUA_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in AQUA_CSPM_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in AQUA_CSPM_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, AquaStrategy] = {
    "EV-741": "hosts_list",
    "EV-742": "images_minimal",
    "EV-743": "partial_metadata",
}
