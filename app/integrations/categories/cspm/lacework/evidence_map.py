"""Evidence codes for Lacework (distinct band EV-731+)."""

from __future__ import annotations

from typing import Literal

LaceworkStrategy = Literal[
    "alerts_list",
    "org_info_minimal",
    "partial_metadata",
]

LACEWORK_CSPM_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-731",
        "name": "Lacework — cloud security alerts (list)",
        "category": "CSPM",
        "api_endpoint": "GET .../api/v2/Alerts",
    },
    {
        "code": "EV-732",
        "name": "Lacework — organization info (connectivity)",
        "category": "CSPM",
        "api_endpoint": "GET .../api/v2/OrganizationInfo",
    },
    {
        "code": "EV-733",
        "name": "Lacework — integration metadata",
        "category": "CSPM",
        "api_endpoint": "POST .../api/v2/access/tokens + API key",
    },
]

ALL_LACEWORK_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in LACEWORK_CSPM_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in LACEWORK_CSPM_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, LaceworkStrategy] = {
    "EV-731": "alerts_list",
    "EV-732": "org_info_minimal",
    "EV-733": "partial_metadata",
}
