"""
Maps evidence_masters.code to Microsoft Defender for Cloud ARM strategies.

EV-711+ reserved for defender_cloud source (no overlap with Prisma EV-701+).
"""

from __future__ import annotations

from typing import Literal

DefenderStrategy = Literal[
    "assessments",
    "secure_scores",
    "partial_metadata",
]

DEFENDER_CSPM_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-711",
        "name": "Microsoft Defender for Cloud — security assessments",
        "category": "CSPM",
        "api_endpoint": "GET .../Microsoft.Security/assessments",
    },
    {
        "code": "EV-712",
        "name": "Microsoft Defender for Cloud — secure scores",
        "category": "CSPM",
        "api_endpoint": "GET .../Microsoft.Security/secureScores",
    },
    {
        "code": "EV-713",
        "name": "Microsoft Defender for Cloud — ARM API session",
        "category": "CSPM",
        "api_endpoint": "OAuth2 client_credentials → management.azure.com",
    },
]

ALL_DEFENDER_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in DEFENDER_CSPM_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in DEFENDER_CSPM_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, DefenderStrategy] = {
    "EV-711": "assessments",
    "EV-712": "secure_scores",
    "EV-713": "partial_metadata",
}
